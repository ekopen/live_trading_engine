# config.py
import os
from dotenv import load_dotenv
load_dotenv() # for when running locally

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ML")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY_ML")
AWS_BUCKET = os.getenv("S3_BUCKET_NAME_ML")
AWS_REGION = os.getenv("AWS_REGION")

CLICKHOUSE_USERNAME = os.getenv('CLICKHOUSE_USERNAME')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD')

FEATURE_DIR = 'feature_data'
MODEL_DIR = 'models'
