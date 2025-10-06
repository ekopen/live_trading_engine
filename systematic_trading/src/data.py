# data.py
# used to get kafka data, clickhouse data, and connect to aws

from config import MARKET_DATA_CLICKHOUSE_IP, KAFKA_IP, AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID, AWS_REGION, AWS_BUCKET, CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD
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

# historical market data
def market_clickhouse_client():      
    client = clickhouse_connect.get_client(
        host=MARKET_DATA_CLICKHOUSE_IP,
        port=8123,
        username=CLICKHOUSE_USERNAME,   
        password=CLICKHOUSE_PASSWORD,
        database="default"
    )
    return client

# portfolio data
def trading_clickhouse_client():
    return clickhouse_connect.get_client(
        host="clickhouse",
        # host="localhost",
        port=8123,
        username=CLICKHOUSE_USERNAME,
        password=CLICKHOUSE_PASSWORD,
        database="default"
    )

# # real time market data
# def get_kafka_data(kafka_topic, group_id):
#     consumer = KafkaConsumer(
#         kafka_topic,
#         bootstrap_servers=[KAFKA_IP],
#         auto_offset_reset="latest",   
#         enable_auto_commit=False,   
#         group_id=group_id,
#     )
#     return consumer

# # return latest message from the consumer (this should be optimized to "hang")
# def get_latest_price(consumer):
#     consumer.poll(timeout_ms=100)
#     try:
#         for tp in consumer.assignment():
#             consumer.seek_to_end(tp)
#         msg = next(consumer)
#         return json.loads(msg.value.decode("utf-8")).get("price")
#     except Exception:
#         logger.exception("Error getting latest message from Kafka consumer")
#         return None
    
latest_prices = {}

def start_price_listener(kafka_topic, group_id, stop_event, symbols=None):
    consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers=[KAFKA_IP],   # adjust with your KAFKA_IP
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
                latest_prices[sym] = data["price"]
        consumer.close()

    threading.Thread(target=run, daemon=True).start()

def get_latest_price(symbol):
    return latest_prices.get(symbol)