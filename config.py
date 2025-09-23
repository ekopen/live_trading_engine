# config.py
# variables that are used across the project

KAFKA_BOOTSTRAP_SERVER="159.65.41.22:9092"

CLICKHOUSE_DURATION = (60 * 60 * 24 * 7)  # how old data can be in Clickhouse before it will be moved to a parquet (seconds)
ARCHIVE_FREQUENCY = (60 * 60 * 24)  # how often we check for old data to move to parquet and upload to cloud (seconds)
HEARTBEAT_FREQUENCY = 60 # seconds per heartbeat, where we record diagnostics and monitoring data 

WS_LAG_THRESHOLD = 1.5 # amount of websocket lag considered a spike
PROC_LAG_THRESHOLD = 3 # amount of processing lag considered a spike
