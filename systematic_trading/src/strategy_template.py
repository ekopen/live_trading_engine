# strategy_template.py
#  contains a default class for all strategies

import threading, logging, time, os, random
import numpy as np
from data import get_latest_price, clickhouse_client
from portfolio import portfolio_monitoring, get_cash_balance, get_qty_balance, get_pv_value, update_status
from ml_functions import get_production_data, build_features, get_ml_model
from execution import execute_trade
logger = logging.getLogger(__name__)

class StrategyTemplate:

    def __init__(self, stop_event, kafka_topic, symbol, strategy_name, starting_cash, starting_mv, monitor_frequency, strategy_description, execution_frequency, allocation_pct, reset_interval, s3_key, local_path, LSTM_flag, max_streak):
        self.stop_event = stop_event
        self.kafka_topic = kafka_topic
        self.symbol = symbol
        self.symbol_raw = f"BINANCE:{self.symbol}USDT"
        self.strategy_name = strategy_name
        self.starting_cash = starting_cash
        self.starting_mv = starting_mv
        self.monitor_frequency = monitor_frequency
        self.strategy_description = strategy_description
        self.execution_frequency = execution_frequency
        self.allocation_pct = allocation_pct
        self.s3_key = s3_key
        self.local_path = local_path
        self.last_reset = time.time()
        self.reset_interval = reset_interval
        self.LSTM_flag = LSTM_flag
        self.max_streak = max_streak

    def start_portfolio_monitoring(self):
        logger.info(f"Beginning position monitoring for {self.symbol}, {self.strategy_name}.")
        try:
            client = clickhouse_client()
            portfolio_monitoring(self.stop_event, self.monitor_frequency, self.symbol, self.symbol_raw, self.strategy_name, client)
        except Exception as e:
            logger.exception(f"Error beginning position monitoring for {self.symbol}, {self.strategy_name}: {e}")

    def close_position(self, client):
        logger.info(f"Closing position for {self.symbol}, {self.strategy_name}.")
        try:
            current_price = get_latest_price(self.symbol_raw)
            qty = get_qty_balance(client, self.strategy_name, self.symbol)
            if qty < 0:
                decision = "BUY"
            elif qty > 0:
                decision = "SELL"
            else:
                decision = "HOLD"
            qty = abs(qty)
            execution_logic = (
                f"Closing position for: {self.strategy_name} - {self.symbol}\n"
                f"Current quantity of {self.symbol} is {qty}, executing a {decision}\n"
                f"Model price: {current_price:.2f}"
            )
            execute_trade(client, decision, current_price, qty, self.strategy_name, self.symbol, self.symbol_raw, execution_logic, slippage_flag="N") 
            update_status(client, self.strategy_name, self.symbol, 'closed')
        except Exception as e:
            logger.exception(f"Error closing position for {self.symbol}, {self.strategy_name}: {e}")
        
    def long_only_strategy(self, client):
        logger.info(f"Running Long Only buy-and-hold strategy for {self.symbol}, {self.strategy_name}.")
        update_status(client, self.strategy_name, self.symbol, 'active')
        try:
            current_price = get_latest_price(self.symbol_raw)
            qty_owned = get_qty_balance(client, self.strategy_name, self.symbol)
            if qty_owned == 0:
                cash_balance = get_cash_balance(client, self.strategy_name, self.symbol)

                qty = (cash_balance * self.allocation_pct) / current_price

                execution_logic = (
                    f"{self.strategy_name} - {self.symbol} decision: BUY\n"
                    f"Buy-and-hold benchmark, model price: {current_price:.2f}"
                )

                execute_trade(client, "BUY", current_price, qty, self.strategy_name, self.symbol, self.symbol_raw, execution_logic, slippage_flag="N")
                logger.info(f"{self.strategy_name} initial BUY executed for {self.symbol}. Holding position now.")
            else:
                logger.info(f"{self.strategy_name} already holds {qty_owned} {self.symbol}. No further trades.")
            
            while not self.stop_event.is_set():
                if self.stop_event.wait(self.execution_frequency):
                    break

        except Exception as e:
            logger.exception(f"Error in Long Only strategy for {self.symbol}: {e}")
        finally:
            self.close_position(client)
            logger.info(f"Long Only strategy shutting down for {self.symbol}.")

    def ml_strategy(self, client):
        logger.info(f"Beginning strategy signal generation for {self.symbol}, {self.strategy_name}.")
        update_status(client, self.strategy_name, self.symbol, 'active')
        # because I am having trouble with the ml models getting stuck in a loop of same decision, adding a manual override to show activity
        last_decision = None
        decision_streak = 1
        try:
            while not self.stop_event.is_set():
                # RESET LOGIC
                now = time.time()
                if now - self.last_reset > self.reset_interval:
                    self.close_position(client)
                    self.last_reset = now
                    continue

                # GET PRODUCTION DATA
                prod_df = get_production_data(client, self.symbol_raw)
                feature_df = build_features(prod_df)
                feature_df_clean = feature_df.drop(columns=["price", "minute"]).tail(1)
                if feature_df_clean.empty:
                    logger.warning(f"Feature dataframe for {self.symbol} is empty after cleaning. Skipping iteration.")
                    if self.stop_event.wait(self.execution_frequency):
                        break
                    continue

                # GET MODEL
                ml_model = get_ml_model(self.s3_key, self.local_path, self.LSTM_flag)
                if ml_model is None:
                    logger.warning(f"No ML model found for {self.symbol}. Skipping iteration.")
                    if self.stop_event.wait(self.execution_frequency):
                        break
                    continue

                # get probabilities to scale qty size based on confidence
                try:
                    if not self.LSTM_flag: # non LSTM case
                        probs = ml_model.predict_proba(feature_df_clean.values)[0]
                    else: # LSTM case
                        X = feature_df_clean.values
                        X = np.expand_dims(X, axis=-1)
                        preds = ml_model.predict(X)
                        probs = preds[0]

                    pred_class = np.argmax(probs)
                    conf = np.max(probs)

                except Exception as e:
                    logger.warning(f"Model prediction failed for {self.symbol} {self.strategy_name}: {e}")
                    if self.stop_event.wait(self.execution_frequency):
                        break
                    continue

                logger.info(f"{self.strategy_name} - Raw probabilities: {probs}")
                logger.info(f"{self.strategy_name} - pred_class: {pred_class}, conf: {conf}") 

                # Map to decision
                if pred_class == 2:
                    decision = "BUY"
                elif pred_class == 0:
                    decision = "SELL"
                else:
                    decision = "HOLD"
                # Track consecutive same actions
                if decision == last_decision:
                    decision_streak += 1
                else:
                    decision_streak = 1  # reset if action changes
                last_decision = decision
                # Force a change if stuck too long
                if decision_streak >= self.max_streak:
                    logger.info(f"Decision {decision} repeated {decision_streak} times — forcing change.")
                    if decision == "HOLD":
                        decision = random.choice(["BUY", "SELL"])
                    elif decision == "BUY":
                        decision = "SELL"
                    else:
                        decision = "BUY"
                    decision_streak = 1
                
                # adjust for confidence interval, scaled by decision streak
                if conf > 0.7:
                    size_factor = 1.0 / decision_streak     
                elif conf > 0.55:
                    size_factor = 0.5 / decision_streak      
                else:
                    size_factor = 0.25 / decision_streak   

                # DETERMINE TRADE SIZE
                current_price = get_latest_price(self.symbol_raw)
                portfolio_value = get_pv_value(client, self.strategy_name, self.symbol)
                qty = (portfolio_value * self.allocation_pct * size_factor) / current_price if decision in ["BUY", "SELL"] else 0

                # RECORD EXECUTION LOGIC
                execution_logic = (
                    f"{self.strategy_name} - {self.symbol} decision: {decision}\n"
                    f"Model price: {current_price:.2f}"
                )

                #SEND TRADE TO EXECTUION ENGINE
                execute_trade(client, decision, current_price, qty, self.strategy_name, self.symbol, self.symbol_raw, execution_logic, slippage_flag="Y")

                # TRADE FREQUENCY
                if self.stop_event.wait(self.execution_frequency):
                    break

        except Exception as e:
            logger.exception(f"Error in {self.strategy_name} - {self.symbol} strategy: {e}")
        finally:
            self.close_position(client)
            logger.info(f"{self.strategy_name} strategy shutting down for {self.symbol}.")

    def run_strategy(self):
        logger.info(f"Running strategy for {self.symbol}, {self.strategy_name}.")
        try:
            client = clickhouse_client()
            t1 = threading.Thread(target=self.start_portfolio_monitoring, daemon=True)
            if self.strategy_name == "Long Only":
                t2 = threading.Thread(target=self.long_only_strategy, args=(client,), daemon=True)
            else:
                t2 = threading.Thread(target=self.ml_strategy, args=(client,), daemon=True)
            t1.start()
            t2.start()
            return [t1, t2]
        except Exception as e:
            logger.exception(f"Error running strategy for {self.symbol}, {self.strategy_name}: {e}")
            return []