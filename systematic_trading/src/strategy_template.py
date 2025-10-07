# strategy_template.py
#  contains a default class for all strategies

import threading, logging, time
import numpy as np
from data import get_latest_price, clickhouse_client
from portfolio import portfolio_monitoring, get_cash_balance, get_qty_balance
from ml_functions import get_production_data, build_features, get_ml_model
from execution import execute_trade
logger = logging.getLogger(__name__)

class StrategyTemplate:

    def __init__(self, stop_event, kafka_topic, symbol, strategy_name, starting_cash, starting_mv, monitor_frequency, strategy_description, execution_frequency, allocation_pct, reset_interval, s3_key, local_path):
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

    def start_portfolio_monitoring(self):
        logger.info(f"Beginning position monitoring for {self.symbol}, {self.strategy_name}.")
        try:
            trading_client = clickhouse_client()
            portfolio_monitoring(self.stop_event, self.monitor_frequency, self.symbol, self.symbol_raw, self.strategy_name, trading_client)
        except Exception as e:
            logger.exception(f"Error beginning position monitoring for {self.symbol}, {self.strategy_name}: {e}")

    def close_position(self, trading_data_client):
        logger.info(f"Closing position for {self.symbol}, {self.strategy_name}.")
        try:
            current_price = get_latest_price(self.symbol_raw)
            qty = get_qty_balance(trading_data_client, self.strategy_name, self.symbol)
            if qty < 0:
                decision = "BUY"
            elif qty > 0:
                decision = "SELL"
            else:
                decision = "HOLD"
            execution_logic = (
                f"Closing position for: {self.strategy_name} - {self.symbol}\n"
                f"Currenty quantity of {self.symbol} is {qty}, executing a {decision}\n"
                f"Model price: {current_price:.2f}"
            )
            execute_trade(trading_data_client, decision, current_price, qty, self.strategy_name, self.symbol, self.symbol_raw, execution_logic) 
        except Exception as e:
            logger.exception(f"Error closing position for {self.symbol}, {self.strategy_name}: {e}")
        
    def long_only_strategy(self, trading_data_client):
        logger.info(f"Running Long Only buy-and-hold strategy for {self.symbol}, {self.strategy_name}.")
        try:
            current_price = get_latest_price(self.symbol_raw)
            qty_owned = get_qty_balance(trading_data_client, self.strategy_name, self.symbol)
            if qty_owned == 0:
                cash_balance = get_cash_balance(trading_data_client, self.strategy_name, self.symbol)

                qty = (cash_balance * self.allocation_pct) / current_price

                execution_logic = (
                    f"{self.strategy_name} - {self.symbol} decision: BUY\n"
                    f"Buy-and-hold benchmark, model price: {current_price:.2f}"
                )

                execute_trade(trading_data_client, "BUY", current_price, qty, self.strategy_name, self.symbol, self.symbol_raw, execution_logic)
                logger.info(f"{self.strategy_name} initial BUY executed for {self.symbol}. Holding position now.")
            else:
                logger.info(f"{self.strategy_name} already holds {qty_owned} {self.symbol}. No further trades.")
            
            while not self.stop_event.is_set():
                if self.stop_event.wait(self.execution_frequency):
                    break

        except Exception as e:
            logger.exception(f"Error in Long Only strategy for {self.symbol}: {e}")
        finally:
            self.close_position(trading_data_client)
            logger.info(f"Long Only strategy shutting down for {self.symbol}.")

    def ml_strategy(self, market_client, trading_data_client):
        logger.info(f"Beginning strategy signal generation for {self.symbol}, {self.strategy_name}.")
        try:
            while not self.stop_event.is_set():
                # RESET LOGIC
                now = time.time()
                if now - self.last_reset > self.reset_interval:
                    self.close_position(trading_data_client)
                    self.last_reset = now
                    continue

                # GET PRODUCTION DATA
                prod_df = get_production_data(market_client, self.symbol_raw)
                feature_df = build_features(prod_df)
                feature_df_clean = feature_df.drop(columns=["price", "minute"]).tail(1)
                if feature_df_clean.empty:
                    logger.warning(f"Feature dataframe for {self.symbol} is empty after cleaning. Skipping iteration.")
                    if self.stop_event.wait(self.execution_frequency):
                        break
                    continue

                # GET MODEL
                ml_model = get_ml_model(self.s3_key, self.local_path)
                if ml_model is None:
                    logger.warning(f"No ML model found for {self.symbol}. Skipping iteration.")
                    if self.stop_event.wait(self.execution_frequency):
                        break
                    continue

                # PREDICT FROM MODEL
                # raw_pred = ml_model.predict(feature_df_clean)
                # raw_pred = np.array(raw_pred)

                # # Normalize prediction shape:
                # if raw_pred.ndim > 1 and raw_pred.shape[1] > 1:  # probability vector
                #     prediction = int(np.argmax(raw_pred, axis=1)[0])
                # elif raw_pred.ndim > 1:  # (n,1) shaped
                #     prediction = int(raw_pred[0][0])
                # else:
                #     prediction = int(raw_pred[0])

                # get probabilities to scale qty size based on confidence
                try:
                    probs = ml_model.predict_proba(feature_df_clean)[0]
                except Exception as e:
                    logger.warning(f"Model prediction failed for {self.symbol}: {e}")
                    if self.stop_event.wait(self.execution_frequency):
                        break
                    continue
                pred_class = probs.argmax()
                conf = probs.max()

                if conf > 0.7:
                    size_factor = 1.0     
                elif conf > 0.55:
                    size_factor = 0.5     
                else:
                    size_factor = 0.25    

                # Map to decision
                if pred_class == 2:
                    decision = "BUY"
                elif pred_class == 0:
                    decision = "SELL"
                else:
                    decision = "HOLD"

                # DETERMINE TRADE SIZE
                current_price = get_latest_price(self.symbol_raw)
                cash_balance = get_cash_balance(trading_data_client, self.strategy_name, self.symbol)
                qty = (cash_balance * self.allocation_pct * size_factor) / current_price if decision in ["BUY", "SELL"] else 0

                # RECORD EXECUTION LOGIC
                execution_logic = (
                    f"{self.strategy_name} - {self.symbol} decision: {decision}\n"
                    f"Model price: {current_price:.2f}"
                )

                #SEND TRADE TO EXECTUION ENGINE
                execute_trade(trading_data_client, decision, current_price, qty, self.strategy_name, self.symbol, self.symbol_raw, execution_logic)

                # TRADE FREQUENCY
                if self.stop_event.wait(self.execution_frequency):
                    break

        except Exception as e:
            logger.exception(f"Error in {self.strategy_name} - {self.symbol} strategy: {e}")
        finally:
            self.close_position(trading_data_client)
            logger.info(f"{self.strategy_name} strategy shutting down for {self.symbol}.")

    def run_strategy(self):
        logger.info(f"Running strategy for {self.symbol}, {self.strategy_name}.")
        try:
            market_client = clickhouse_client()
            trading_client = clickhouse_client()
            t1 = threading.Thread(target=self.start_portfolio_monitoring, daemon=True)
            if self.strategy_name == "Long Only":
                t2 = threading.Thread(target=self.long_only_strategy, args=(trading_client,), daemon=True)
            else:
                t2 = threading.Thread(target=self.ml_strategy, args=(market_client, trading_client), daemon=True)

            t1.start()
            t2.start()
            return [t1, t2]
        except Exception as e:
            logger.exception(f"Error running strategy for {self.symbol}, {self.strategy_name}: {e}")
            return []