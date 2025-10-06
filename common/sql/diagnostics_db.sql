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