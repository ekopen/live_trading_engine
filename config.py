# config.py
# variables that are used across the project

import os

KAFKA_BOOTSTRAP_SERVER="159.65.41.22:9092"

CLICKHOUSE_DURATION = (60 * 60 * 23)  # how old data can be in Clickhouse before it will be moved to a parquet (seconds)
ARCHIVE_FREQUENCY = (60 * 60 * 1)  # how often we check for old data to move to parquet and upload to cloud (seconds)
HEARTBEAT_FREQUENCY = 30 # seconds per heartbeat, where we record diagnostics and monitoring data 

EMPTY_LIMIT = 10 #number of consecutive empty diagnostics records before restarting the system

WS_LAG_THRESHOLD = 1.5 # amount of websocket lag considered a spike
PROC_LAG_THRESHOLD = 3 # amount of processing lag considered a spike
