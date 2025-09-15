# main.py
# starts and stops the data pipeline

# imports
import threading, time, signal, logging
from config import SYMBOL, API_KEY, CLICKHOUSE_DURATION, ARCHIVE_FREQUENCY, HEARTBEAT_FREQUENCY, EMPTY_LIMIT, WS_LAG_THRESHOLD, PROC_LAG_THRESHOLD

from clickhouse import create_ticks_db, create_diagnostics_db, create_diagnostics_monitoring_db, create_uptime_db, new_client
from cloud_migration import migration_to_cloud
from kafka_producer import start_producer
from kafka_consumer import start_consumer
from monitoring import ticks_monitoring, diagnostics_monitoring

# logging 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("log_data/app.log", encoding="utf-8"),
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

        # create clickhouse tables
        create_ticks_db(), create_diagnostics_db(), create_diagnostics_monitoring_db(), create_uptime_db()

        ch = new_client()
        ch.insert('monitoring_db',[("System started",)],column_names=['message'])

        # start ingesting data from the websocket, feed to kafka, and insert to clickhouse
        producer_thread = threading.Thread(target=start_producer, args=(SYMBOL, API_KEY, stop_event))
        consumer_thread = threading.Thread(target=start_consumer, args=(stop_event,))
        producer_thread.start(), consumer_thread.start()
        # misc daemon aka background threads for diagnostics and cloud migration and prometheus monitoring
        threading.Thread(target=ticks_monitoring, args=(stop_event,HEARTBEAT_FREQUENCY), daemon=True).start()
        threading.Thread(target=diagnostics_monitoring, args=(stop_event, HEARTBEAT_FREQUENCY, EMPTY_LIMIT, WS_LAG_THRESHOLD, PROC_LAG_THRESHOLD), daemon=True).start() 
        threading.Thread(target=migration_to_cloud, args=(stop_event,CLICKHOUSE_DURATION, ARCHIVE_FREQUENCY), daemon=True).start() 

        while not stop_event.is_set():
             time.sleep(1)

        ch.insert('monitoring_db',[("System closing",)],column_names=['message'])
        producer_thread.join(timeout=3)
        consumer_thread.join(timeout=3)
        logger.info("System shutdown complete.")

    except Exception as e:
        logger.exception("Fatal error in main loop")
        