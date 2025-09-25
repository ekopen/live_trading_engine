# main.py
# starts and stops the data consumption pipeline

# imports
import threading, time, signal, logging
from config import CLICKHOUSE_DURATION, ARCHIVE_FREQUENCY, HEARTBEAT_FREQUENCY

from setup import new_client
from cloud_migration import migration_to_cloud
from kafka_consumer import start_consumer
from monitoring import ticks_monitoring

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
signal.signal(signal.SIGINT, handle_signal) # CTRL+C shutdown

# start/stop loop
if __name__ == "__main__":
    try:
        logger.info("System starting.")

        ch = new_client()

        # start ingesting data from the websocket, feed to kafka, and insert to clickhouse
        consumer_thread = threading.Thread(target=start_consumer, args=(stop_event,))
        consumer_thread.start()
        # misc daemon aka background threads for diagnostics and cloud migration and prometheus monitoring
        threading.Thread(target=ticks_monitoring, args=(stop_event,HEARTBEAT_FREQUENCY), daemon=True).start()
        threading.Thread(target=migration_to_cloud, args=(stop_event,CLICKHOUSE_DURATION, ARCHIVE_FREQUENCY), daemon=True).start() 

        while not stop_event.is_set():
             time.sleep(1)

        consumer_thread.join(timeout=3)
        logger.info("System shutdown complete.")

    except Exception as e:
        logger.exception("Fatal error in main loop")
        