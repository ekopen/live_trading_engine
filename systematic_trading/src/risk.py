# risk.py
# risk engine module, used to manage risk parameters and ensure trades are executed within defined risk limits

import logging
from config import MAX_DRAWDOWN, MAX_ALLOCATION, MAX_SHORT
from portfolio import get_cash_balance, get_qty_balance
logger = logging.getLogger(__name__)

def check_position_size(client, symbol, qty, direction, price, strategy_name, max_allocation=MAX_ALLOCATION):
    try:
        if strategy_name == 'Long Only':
            return True, "Long Only automatic bypass"

        rows = client.query(f"""
            SELECT portfolio_value , quantity
            FROM portfolio_db_key 
            WHERE strategy_name = '{strategy_name}' AND symbol = '{symbol}'
        """).result_rows
        if not rows or rows[0] is None:
            return False, "Portfolio not initialized for position size check"
        portfolio_value , current_qty = rows[0]
        trade_value = abs(qty * price)

        if trade_value > max_allocation * portfolio_value:
            msg = f"Trade value {trade_value:.2f} exceeds max allocation {max_allocation*100:.1f}% of portfolio {portfolio_value:.2f}"
            logger.warning(msg)
            return False, msg
    except Exception as e:
        logger.exception(f"Error checking position size: {e}")
        return False, "Error in position size check"
    return True, "Position size ok"


def check_cash_balance(client, qty, direction, price, strategy_name, symbol):
    try:
        cash_balance = get_cash_balance(client, strategy_name, symbol)
        trade_cost = qty * price * direction
        current_qty = get_qty_balance(client, strategy_name, symbol)

        if direction == 1 and trade_cost > cash_balance:
            msg = f"Not enough cash. Needed {trade_cost:.2f}, available {cash_balance:.2f}"
            logger.warning(msg)
            return False, msg
    except Exception as e:
        logger.exception(f"Error checking cash balance: {e}")
        return False, "Error in cash balance check"
    return True, "Cash balance ok"

def check_qty_balance(client, qty, direction, price, strategy_name, symbol):
    try:
        quantity = get_qty_balance(client, strategy_name, symbol)
        traded_qty = qty * direction
        if direction == -1 and ((quantity + traded_qty) * price) < -MAX_SHORT:
            msg = f"Short position limit exceeded. Current {quantity}, attempted trade {traded_qty}"
            logger.warning(msg)
            return False, msg
    except Exception as e:
        logger.exception(f"Error checking quantity balance :{e}")
        return False, "Error in quantity balance check"
    return True, "Quantity balance ok"


def check_max_drawdown(client, strategy_name, symbol, max_drawdown=MAX_DRAWDOWN):
    if strategy_name == 'Long Only':
        return True, "Long Only automatic bypass"
    try:
        rows = client.query(f"""
            WITH
                (SELECT MIN(portfolio_value) 
                 FROM portfolio_db_ts 
                 WHERE strategy_name = '{strategy_name}' AND symbol = '{symbol}') AS min_val,
                (SELECT MAX(portfolio_value) 
                 FROM portfolio_db_ts 
                 WHERE strategy_name = '{strategy_name}' AND symbol = '{symbol}') AS max_val,
                (SELECT portfolio_value 
                 FROM portfolio_db_ts 
                 WHERE strategy_name = '{strategy_name}' AND symbol = '{symbol}' 
                 ORDER BY time DESC LIMIT 1) AS latest_val
            SELECT min_val, max_val, latest_val
        """).result_rows
        if not rows or rows[0] is None:
            return False, "Portfolio not initialized for position size check"

        if rows:
            min_val, max_val, latest_val = rows[0]
            if max_val and max_val > 0:
                drawdown = (max_val - latest_val) / max_val
                if drawdown > max_drawdown:
                    msg = f"Max drawdown {drawdown:.2%} exceeded limit {max_drawdown:.0%}"
                    logger.warning(msg)
                    return False, msg
    except Exception as e:
        logger.exception(f"Error checking max drawdown: {e}")
        return False, "Error in drawdown check"
    return True, "Drawdown ok"


def run_risk_checks(client, symbol, qty, direction, model_price, strategy_name):
    try:
        checks = [
            check_position_size(client, symbol, qty, direction, model_price, strategy_name),
            check_cash_balance(client, qty, direction,
            model_price, strategy_name, symbol),
            check_qty_balance(client, qty, direction,
            model_price, strategy_name, symbol),
            check_max_drawdown(client, strategy_name, symbol)
        ]

        failures = []
        for success, msg in checks:
            if not success:
                failures.append(msg)
        all_passed = len(failures) == 0
        return all_passed, failures
    except Exception as e:
        logger.exception(f"Error running risk checks: {e}")
        return False, ["Error in risk checks"]
