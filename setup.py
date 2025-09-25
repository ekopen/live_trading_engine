# setup.py
# one off container to run at the start
# docker compose run --rm db_setup

from config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
import clickhouse_connect
import logging
import boto3
logger = logging.getLogger(__name__)

s3 = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def new_client():
    return clickhouse_connect.get_client(
        host="clickhouse", #clickhouse for docker, localhost for local dev 
        port=8123,
        username="default",
        password="mysecurepassword",
        database="default"
    )

def delete_tables():
    ch = new_client()
    ch.command("DROP TABLE IF EXISTS ticks_db SYNC")
    ch.command("DROP TABLE IF EXISTS websocket_diagnostics SYNC")
    ch.command("DROP TABLE IF EXISTS processing_diagnostics SYNC")
    ch.command("DROP TABLE IF EXISTS monitoring_db SYNC")
    ch.command("DROP TABLE IF EXISTS uptime_db SYNC")

def create_ticks_db():
    ch = new_client()
    ch.command('''
    CREATE TABLE IF NOT EXISTS ticks_db(
        timestamp       DateTime64(3, 'UTC'),
        timestamp_ms    Int64,
        symbol          String,
        price           Float64,
        volume          Float64,
        received_at     DateTime64(3, 'UTC'),
        insert_time     DateTime64(3, 'UTC') DEFAULT now64(3)
    ) 
    ENGINE = MergeTree()
    PARTITION BY toYYYYMMDD(timestamp)
    ORDER BY timestamp_ms
    TTL toDateTime(timestamp) + INTERVAL 7 DAY DELETE
    ''')

def create_diagnostics_db():
    ch = new_client()
    ch.command(f"""
    CREATE TABLE IF NOT EXISTS websocket_diagnostics (
        avg_timestamp Nullable(DateTime64(3, 'UTC')),
        avg_received_at Nullable(DateTime64(3, 'UTC')),
        avg_websocket_lag Nullable(Float64),
        message_count Float64,
        diagnostics_timestamp    DateTime64(3, 'UTC') DEFAULT now64(3)
    )
    ENGINE = MergeTree()
    PARTITION BY toYYYYMMDD(toDate(diagnostics_timestamp))
    ORDER BY diagnostics_timestamp
    TTL toDateTime(diagnostics_timestamp) + INTERVAL 7 DAY DELETE
    """)

    ch.command(f"""
    CREATE TABLE IF NOT EXISTS processing_diagnostics (
        avg_timestamp Nullable(DateTime64(3, 'UTC')),
        avg_received_at Nullable(DateTime64(3, 'UTC')),
        avg_processed_timestamp Nullable(DateTime64(3, 'UTC')),
        avg_processing_lag Nullable(Float64),
        message_count Float64,
        diagnostics_timestamp    DateTime64(3, 'UTC') DEFAULT now64(3)
    )
    ENGINE = MergeTree()
    PARTITION BY toYYYYMMDD(toDate(diagnostics_timestamp))
    ORDER BY diagnostics_timestamp
    TTL toDateTime(diagnostics_timestamp) + INTERVAL 7 DAY DELETE
    """)

# try:
#     logger.info("Deleting tables.")
#     delete_tables()
# except Exception:
#     logger.warning("Error when deleting tables.")

try:
    logger.info("Creating tables.")
    create_ticks_db(), create_diagnostics_db()
except Exception:
    logger.warning("Error when creating tables.")

# add table modification