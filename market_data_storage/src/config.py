# config.py
import os

KAFKA_BOOTSTRAP_SERVER="kafka:19092"

CLICKHOUSE_DURATION = (60 * 60 * 24 * 7)  # how old data can be in Clickhouse before it will be moved to a parquet (seconds)
ARCHIVE_FREQUENCY = (60 * 60 * 24)  # how often we check for old data to move to parquet and upload to cloud (seconds)
HEARTBEAT_FREQUENCY = 60 # seconds per heartbeat, where we record diagnostics and monitoring data 

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

CLICKHOUSE_USERNAME = os.getenv('CLICKHOUSE_USERNAME')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD')
