# kakfa_consumer.py
# kafka consumer that reads from the price_ticks topic and inserts into clickhouse

from config import KAFKA_BOOTSTRAP_SERVER
from kafka import KafkaConsumer
import json, time, logging
from datetime import datetime, timezone
from clickhouse import new_client
logger = logging.getLogger(__name__)

# prepares the data for clickhouse
def validate_and_parse(data):

    timestamp_dt = datetime.fromisoformat(data['timestamp']).astimezone(timezone.utc)
    received_at_dt = datetime.fromisoformat(data['received_at']).astimezone(timezone.utc)

    # return a tuple in the exact order of table schema:
    return (
        timestamp_dt,                  # DateTime
        data['timestamp_ms'],          # Int64
        data['symbol'],                # String
        float(data['price']),          # Float64
        float(data['volume']),         # Float64
        received_at_dt                 # DateTime
    )

def start_consumer(stop_event):

    logger.info("Kafka consumer started.")

    ch_client = new_client()

    consumer = KafkaConsumer(
        'price_ticks', # subscribe to the topic
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVER],
        group_id='market_data_storage',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        enable_auto_commit=False,
        auto_offset_reset="latest",
    )

    #using batching to improve performance
    batch = []
    last_flush = time.time()
    BATCH_SIZE = 500
    FLUSH_INTERVAL = 1  # seconds

    try:
        while not stop_event.is_set():
            records = consumer.poll(timeout_ms=500) # wait for messages
            if not records:
                continue # if not records, continue to next iteration
            for tp, messages in records.items(): # get messages from each partition
                for message in messages:
                    try:
                        validated_row = validate_and_parse(message.value)
                        batch.append(validated_row)

                        if len(batch) >= BATCH_SIZE or (time.time() - last_flush) > FLUSH_INTERVAL:
                            ch_client.insert(
                                'ticks_db',
                                batch,
                                column_names=['timestamp','timestamp_ms','symbol','price','volume','received_at']
                            )
                            logger.info(f"Inserted {len(batch)} rows to ticks_db.")
                            batch.clear()
                            last_flush = time.time()
                    except Exception as e:
                        logger.exception("Consumer parse/insert error")
    finally:
        try:
            if batch:
                ch_client.insert(
                    'ticks_db',
                    batch,
                    column_names=['timestamp','timestamp_ms','symbol','price','volume','received_at']
                )
                logger.info(f"Inserted final {len(batch)} rows.")
        except Exception:
            logger.exception("Final batch insert failed")
        logger.info("Closing consumer.")
        try:
            consumer.close()
        except Exception:
            logger.exception(f"Error closing consumer during shutdown")






