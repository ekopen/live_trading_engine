# ml_function.py
# fetches ml models and generates feature data for them

from config import MODEL_REFRESH_INTERVAL
from data import s3, bucket_name
from tensorflow.keras.models import load_model
import logging, joblib, time, os
logger = logging.getLogger(__name__)

# cache state
cached_models = {}
last_refresh_times = {}

def get_production_data(client, symbol):
    try:
        df = client.query_df(f"""
            SELECT *
            FROM (
                SELECT
                    minute,
                    anyHeavyMerge(open)   AS price
                FROM minute_bars
                WHERE symbol = '{symbol}' AND minute >= now() - INTERVAL 2 HOUR
                GROUP BY minute
                ORDER BY minute DESC
                LIMIT 120
            ) sub
            ORDER BY minute ASC
        """)
        return df
    except Exception as e:
        logger.exception(f"Error fetching production data for {symbol}: {e}")
        return None


def build_features(df):
    try:
        # standard features
        df["returns"] = df["price"].pct_change()
        df["sma_30"] = df["price"].rolling(window=30).mean()
        df["sma_60"] = df["price"].rolling(window=60).mean()
        df["momentum_10"] = df["price"] / df["price"].shift(10) - 1
        df["momentum_30"] = df["price"] / df["price"].shift(30) - 1
        df["volatility_30"] = df["returns"].rolling(window=30).std()
        for lag in [1, 2, 5]:
            df[f"lag_return_{lag}"] = df["returns"].shift(lag)

        # RSI
        delta = df["price"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi_14"] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = df["price"].ewm(span=12, adjust=False).mean()
        ema26 = df["price"].ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

        # STATIONARY FEATURES
        df["price_change"] = df["price"].diff()
        df["sma_ratio"] = df["sma_30"] / df["sma_60"] - 1
        df["macd_diff"] = df["macd"] - df["macd_signal"]

        # Smoothed return signal
        df["ema_return_10"] = df["returns"].ewm(span=10, adjust=False).mean()

        # Rolling z-score of returns
        df["zscore_30"] = (df["returns"] - df["returns"].rolling(30).mean()) / df["returns"].rolling(30).std()

        # Directional signal (momentum vs volatility)
        df["dir_strength"] = df["momentum_10"] / (df["volatility_30"] + 1e-8)
            
        df = df.dropna()
        return df
    except Exception as e:
        logger.exception(f"Error building features: {e}")
        return None

def get_ml_model(s3_key, local_path, LSTM_flag):
    try:
        now = time.time()

        if (
            s3_key in cached_models and
            (now - last_refresh_times.get(s3_key, 0)) < MODEL_REFRESH_INTERVAL
        ):
            return cached_models[s3_key]

        # otherwise, refresh
        logger.info(f"Downloading model {s3_key} from S3...")
        # s3.download_file(bucket_name, s3_key, local_path) #turning off for cost purposes

        if LSTM_flag:
            ml_model = load_model(local_path)
        else:
            ml_model = joblib.load(local_path)

        # update cache
        cached_models[s3_key] = ml_model
        last_refresh_times[s3_key] = now

        return ml_model

    except Exception as e:
        logger.exception(f"Error loading ML model from S3 for {s3_key}")
        return None
