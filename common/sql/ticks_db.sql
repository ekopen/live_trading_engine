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
TTL toDateTime(timestamp) + INTERVAL 9 DAY DELETE