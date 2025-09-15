# clickhouse.py
# creates pricing database

import clickhouse_connect
import logging
logger = logging.getLogger(__name__)

def new_client():
    return clickhouse_connect.get_client(
        host="clickhouse", #clickhouse for docker, localhost for local dev 
        port=8123,
        username="default",
        password="mysecurepassword",
        database="default"
    )

def create_ticks_db():

    logger.info("Creating ticks_db table.")
    ch = new_client()
    # ch.command("DROP TABLE IF EXISTS ticks_db SYNC")
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
    TTL toDateTime(timestamp) + INTERVAL 1 DAY DELETE
    ''')
    logger.info("ticks_db table created successfully.")

def create_diagnostics_db():

    logger.info("Creating websocket_diagnostics table.")
    ch = new_client()
    # ch.command("DROP TABLE IF EXISTS websocket_diagnostics SYNC")
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
    TTL toDateTime(diagnostics_timestamp) + INTERVAL 1 DAY DELETE
    """)
    logger.info("websocket_diagnostics table created successfully.")

    logger.info("Creating processing_diagnostics table.")
    # ch.command("DROP TABLE IF EXISTS processing_diagnostics SYNC")
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
    TTL toDateTime(diagnostics_timestamp) + INTERVAL 1 DAY DELETE
    """)
    logger.info("processing_diagnostics table created successfully.")

def create_diagnostics_monitoring_db():

    logger.info("Creating monitoring_db table.")
    ch = new_client()
    # ch.command("DROP TABLE IF EXISTS monitoring_db SYNC")
    ch.command('''
    CREATE TABLE IF NOT EXISTS monitoring_db(
        monitoring_timestamp     DateTime64(3, 'UTC') DEFAULT now64(3),
        message    String
    ) 
    ENGINE = MergeTree()
    PARTITION BY toYYYYMMDD(monitoring_timestamp)
    ORDER BY monitoring_timestamp
    TTL toDateTime(monitoring_timestamp) + INTERVAL 1 DAY DELETE
    ''')
    logger.info("monitoring_db table created successfully.")

def create_uptime_db():

    logger.info("Creating uptime_db table.")
    ch = new_client()
    # ch.command("DROP TABLE IF EXISTS uptime_db SYNC")
    ch.command('''
    CREATE TABLE IF NOT EXISTS uptime_db(
        uptime_timestamp   DateTime64(3, 'UTC'),
        is_up              UInt8
    )
    ENGINE = MergeTree()
    PARTITION BY toYYYYMMDD(uptime_timestamp)
    ORDER BY uptime_timestamp
    TTL toDateTime(uptime_timestamp) + INTERVAL 1 DAY DELETE
    ''')
    logger.info("uptime_db table created successfully.")
