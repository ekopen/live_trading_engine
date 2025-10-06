# main.py
# starts running the ML pipeline

import threading, signal, logging, schedule, time
from ml_models import get_ml_models
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

# start/stop loop
if __name__ == "__main__":
    logger.info("System starting.")
    try:
        
        model_arr = get_ml_models(stop_event)

        for model in model_arr:
            logger.info(f"Registering jobs for {model.model_name_key}")
            schedule.every(model.retrain_interval).hours.do(model.create_feature_data)
            schedule.every(model.retrain_interval).hours.do(model.train_models)

            model.create_feature_data()
            model.train_models()

        while not stop_event.is_set():
             time.sleep(1)

        logger.info("System shutdown complete.") 

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down...")
        stop_event.set()
    except Exception:
        logger.exception("Fatal error in main loop")
        