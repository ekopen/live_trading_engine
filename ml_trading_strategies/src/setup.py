# setup.py

from config import MARKET_DATA_CLICKHOUSE_IP, AWS_ACCESS_KEY, AWS_SECRET_KEY, CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD
import clickhouse_connect
import logging, boto3
logger = logging.getLogger(__name__)

def clickhouse_client():
    return clickhouse_connect.get_client(
        host="clickhouse", #clickhouse for docker, localhost for local dev 
        port=8123,
        username=CLICKHOUSE_USERNAME,
        password=CLICKHOUSE_PASSWORD,
        database="default"
    )

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)
