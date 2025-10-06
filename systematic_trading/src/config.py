# config.py
# variables that are used across the project
import os
from dotenv import load_dotenv
load_dotenv() # for when running locally

SYMBOLS = ["BINANCE:BTCUSDT","BINANCE:ETHUSDT","BINANCE:ADAUSDT","BINANCE:XRPUSDT","BINANCE:SOLUSDT"]

MODEL_REFRESH_INTERVAL = 60 * 60 * 4 # how often to refresh ml models, in seconds

MAX_DRAWDOWN = .5 #maximum amount of portfolio value willing to lose before pausing trading
MAX_ALLOCATION = .5 #maxmimum amount of value per trade compared to portfolio value willing to make
MAX_SHORT = 200000 #max short value of any portfolio

MONITORING_FREQUENCY = 60 #how often to record pf data to the time series

KAFKA_BOOTSTRAP_SERVER="kafka:19092"

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ML")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_KEY_ML")
AWS_BUCKET = os.getenv("S3_BUCKET_NAME_ML")
AWS_REGION = os.getenv("AWS_REGION")

CLICKHOUSE_USERNAME = os.getenv('CLICKHOUSE_USERNAME')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD')



