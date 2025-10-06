# portfolio.py
# Portfolio management module, used to manage portfolio data, update portfolio based on executed trades, and monitor portfolio performance

from data import get_latest_price
import logging, time
logger = logging.getLogger(__name__)

def portfolio_key_order_update(client, symbol, quantity_change, market_value_change, strategy_name):
    try:
        client.command(f"""
            ALTER TABLE portfolio_db_key UPDATE quantity = quantity + {quantity_change}, market_value = market_value + {market_value_change}, cash_balance = cash_balance + {-market_value_change}, portfolio_value = cash_balance + market_value
            WHERE symbol = '{symbol}' AND strategy_name = '{strategy_name}'
        """)
    except Exception as e:
        logger.exception(f"Error updating portfolio key table in ClickHouse: {e}")

def portfolio_monitoring(stop_event, frequency, symbol, symbol_raw, strategy_name, client):
    logger.info("Starting portfolio monitoring thread.")
    while not stop_event.is_set():
        try:
            price = get_latest_price(symbol_raw)
            # Update key table
            client.command(f"""
                ALTER TABLE portfolio_db_key 
                UPDATE market_value = quantity * {price}, 
                       portfolio_value = cash_balance + market_value
                WHERE symbol = '{symbol}' AND strategy_name = '{strategy_name}'
            """)

            # Insert latest values into timeseries table
            rows = client.query(f"""
                SELECT cash_balance, symbol, quantity, market_value, strategy_name, portfolio_value
                FROM portfolio_db_key
                WHERE symbol = '{symbol}' AND strategy_name = '{strategy_name}'
            """).result_rows

            if rows:
                client.insert(
                    "portfolio_db_ts",
                    rows,
                    column_names=[
                        "cash_balance", "symbol", "quantity", "market_value", "strategy_name", "portfolio_value"
                    ]
                )

        except Exception as e:
            logger.exception(f"Error during portfolio monitoring iteration: {e}")

        time.sleep(frequency)

    try:
        logger.info("Portfolio monitoring shutting down.")
    except Exception as e:
        logger.exception(f"Error during portfolio monitoring shutdown: {e}")

def get_cash_balance(client, strategy_name, symbol):
    try:
        rows = client.query(f"""
            SELECT cash_balance 
            FROM portfolio_db_key 
            WHERE strategy_name = '{strategy_name}' AND symbol = '{symbol}'
        """).result_rows
        cash_balance = rows[0][0]
        return cash_balance
    except Exception as e:
        logger.exception(f"Error retrieving cash balance: {e}")

def get_qty_balance(client, strategy_name, symbol):
    try:
        rows = client.query(f"""
            SELECT quantity 
            FROM portfolio_db_key 
            WHERE strategy_name = '{strategy_name}' AND symbol = '{symbol}'
        """).result_rows
        quantity = rows[0][0]
        return quantity
    except Exception as e:
        logger.exception(f"Error retrieving quantity balance: {e}")