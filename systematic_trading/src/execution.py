# execution.py
# Execution engine module, used to execute trades based on signals from the signal engine within parameters set by the risk management module

import logging, time
logger = logging.getLogger(__name__)
from portfolio import portfolio_key_order_update
from data import get_latest_price
from risk import run_risk_checks

def update_execution(client, symbol, execution_logic, quantity, model_price, execution_price, strategy_name, approval_status, approval_comment):
    try:
        arr = [symbol, execution_logic, quantity, model_price, execution_price, strategy_name, approval_status, approval_comment]
        column_names = ["symbol", "execution_logic", "quantity", "model_price","executed_price", "strategy_name", "approval_status", "approval_comment"]
        client.insert("execution_db", [arr], column_names)
    except Exception as e:
        logger.exception(f"Error inserting updating execution records: {e}")

def execute_trade(client, signal, model_price, qty, strategy_name, symbol, symbol_raw, execution_logic, slippage_flag):
    try:
        if signal == "BUY":
            direction = 1
        elif signal == "SELL":
            direction = -1
        else:
            direction = 0

        # check risks of trade
        passed, failures = run_risk_checks(client, symbol, qty, direction, model_price, strategy_name)
        if passed:
            approval_status = "Y"
            approval_comment = "Approved"
        else:
            approval_status = "N"
            approval_comment = "; ".join(failures)
            
        quantity_change = qty * direction
        if approval_status == "Y":
            # in a real system, this is where the order would be routed to the exchange/broker. to simulate real conditions, we just wait a second and get the latest price again
            time.sleep(1)
            if slippage_flag == "N":
                execution_price = model_price  # simulate  execution at model price for long only/closing positions (for simplicity)
            else:
                execution_price = get_latest_price(symbol_raw) # simulatedslippage conditions
            market_value_change = qty * direction * execution_price
            portfolio_key_order_update(client, symbol, quantity_change, market_value_change , strategy_name)
            update_execution(client, symbol, execution_logic, qty * direction, model_price, execution_price, strategy_name, approval_status, approval_comment)
            logger.info(f"Trade executed and recorded. Signal: {signal}, Model Price: {model_price}, Execution Price: {execution_price}, Quantity: {qty}, Strategy: {strategy_name}, Symbol: {symbol}")
        if approval_status == "N":
            update_execution(client, symbol, execution_logic, quantity_change, model_price, None, strategy_name, approval_status, approval_comment)
            logger.warning(f"Trade not approved. Signal: {signal}, Model Price: {model_price}, Quantity: {qty}, Strategy: {strategy_name}, Symbol: {symbol}")
            
    except Exception as e:
        logger.exception(f"Error executing trade: {e}")