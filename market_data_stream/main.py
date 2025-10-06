# main.py
# starts and stops the data stream

# imports
import threading, time, signal, logging
from config import SYMBOLS, API_KEY
from kafka_producer import start_producer

from logging.handlers import RotatingFileHandler
# logging 
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

# start/stop loop
if __name__ == "__main__":
    try:
        logger.info("System starting.")

        # start ingesting data from the websocket and feed to kafka
        producer_thread = threading.Thread(target=start_producer, args=(SYMBOLS, API_KEY, stop_event))
        producer_thread.start()

        while not stop_event.is_set():
             time.sleep(1)

        producer_thread.join(timeout=3)
        logger.info("System shutdown complete.")

    except Exception as e:
        logger.exception("Fatal error in main loop")
        