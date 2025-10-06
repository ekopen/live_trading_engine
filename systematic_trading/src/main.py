# main.py
# starts and stops the trading module

from config import SYMBOLS
import threading, time, signal, logging
from data import start_price_listener
from strategies import get_strategies
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        RotatingFileHandler(
            "log_data/app.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB per file
            backupCount=3,
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# shutdown
stop_event = threading.Event()
def handle_signal(signum, frame):
    logger.info("Received stop signal. Shutting down...")
    stop_event.set()
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal) # CTRL+C shutdown

strategy_arr = get_strategies(stop_event)

# start/stop loop
if __name__ == "__main__":
    try:
        logger.info("System starting.")

        start_price_listener(kafka_topic="price_ticks", group_id="trading-module-listener", stop_event=stop_event, symbols=SYMBOLS)

        # start trading strategies
        all_threads = []
        for strat in strategy_arr:
            all_threads.extend(strat.run_strategy())

        while not stop_event.is_set():
             time.sleep(1)

        logger.info("Stop event set. Waiting for threads to finish...")
        for t in all_threads:
            t.join()
        logger.info("System shutdown complete.") 

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down...")
        stop_event.set()
    except Exception as e:
        logger.exception(f"Fatal error in main loop: {e}")
        