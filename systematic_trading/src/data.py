# data.py
# used to get kafka data, clickhouse data, and connect to aws

from config import AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID, AWS_REGION, AWS_BUCKET, CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD, KAFKA_BOOTSTRAP_SERVER
import clickhouse_connect
from kafka import KafkaConsumer
import logging, json, boto3, threading
logger = logging.getLogger(__name__)

# aws connection
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)
bucket_name = AWS_BUCKET

def clickhouse_client():      
    client = clickhouse_connect.get_client(
        host="clickhouse",
        port=8123,
        username=CLICKHOUSE_USERNAME,   
        password=CLICKHOUSE_PASSWORD,
        database="default"
    )
    return client
    
latest_prices = {}

def start_price_listener(kafka_topic, group_id, stop_event, symbols=None):
    consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVER],
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id=group_id,
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    def run():
        for msg in consumer:
            if stop_event.is_set():
                break
            data = msg.value
            sym = data["symbol"]
            if not symbols or sym in symbols:
                price = data.get("price")
                if isinstance(price, (int, float)):
                    latest_prices[sym] = price
        consumer.close()

    threading.Thread(target=run, daemon=True).start()

def get_latest_price(symbol):
    return latest_prices.get(symbol)