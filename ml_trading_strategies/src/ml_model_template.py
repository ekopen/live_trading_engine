# ml_model_template.py
# contains a default class for all ml models

from config import FEATURE_DIR, MODEL_DIR
from setup import clickhouse_client
from features import get_data, build_features, create_labels
from training import load_dataset, train_and_eval, upload_to_cloud
from tensorflow.keras.models import save_model
import joblib
import logging
logger = logging.getLogger(__name__)

class ML_Model_Template:

    def __init__(self, stop_event, model_name, model_description, symbol, model, retrain_interval, model_save_type):
        self.stop_event = stop_event
        self.model_name = model_name
        self.model_description = model_description
        self.symbol = symbol
        self.symbol_raw = f"BINANCE:{self.symbol}USDT"
        self.model_name_key = f"{self.model_name}-{self.symbol}"
        self.model = model
        self.retrain_interval = retrain_interval # in hours
        self.model_save_type = model_save_type  #h5 or pkl
        self.feature_dir = f'{FEATURE_DIR}/{self.model_name_key}-feature_data.parquet'
        self.model_dir = f'{MODEL_DIR}/{self.model_name_key}-model.{self.model_save_type}'

    # saves a feature parquet locally for model training
    def create_feature_data(self):
        logger.info("Creating feature data.")
        try:
            client = clickhouse_client()
            df = get_data(client, self.symbol_raw)
            df_features = build_features(df)
            df_labels, counts = create_labels(df = df_features, horizon=20, buy_q=.75, sell_q=.25) # this could be modularized
            df_labels.to_parquet(self.feature_dir, index=False)
            logger.info(f"Label distribution for {self.model_name_key} (SELL=0, HOLD=1, BUY=2): {counts.to_dict()}")
            logger.info(f"Finished creating feature data for {self.model_name_key}.")
        except Exception as e:
            logger.exception(f"Feature pipeline failed for {self.model_name_key}: {e}")

    # trains all models, saves them locally, and uploads to cloud
    def train_models(self):
        logger.info(f"Training model for {self.model_name_key}")
        try:
            client = clickhouse_client()
            X, y = load_dataset(self.feature_dir)
            if len(X) < 1440:  # at least 1 day of minute data to train
                logger.warning(f"Not enough data to train {self.model_name_key}. Needed 1440 rows, got {len(X)}. Skipping training.")
                return
            train_and_eval(X, y, self.model,  self.model_name_key, self.model_description, client, self.model_dir, self.retrain_interval)
            if self.model_save_type == 'h5':
                self.model.model_.save(self.model_dir)
            elif self.model_save_type == 'pkl':
                joblib.dump(self.model, self.model_dir)
            upload_to_cloud(self.model_dir)
            logger.info(f"Finished training model for {self.model_name_key}.")
        except Exception as e:
            logger.exception(f"Model training failed for {self.model_name_key}: {e}")