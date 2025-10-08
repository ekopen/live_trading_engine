CREATE TABLE IF NOT EXISTS execution_db (
    time DateTime DEFAULT now(),
    symbol String,
    execution_logic String,
    quantity Float64,
    model_price Float64,
    executed_price Nullable(Float64),
    strategy_name String,
    approval_status String,
    approval_comment String
    ) 
ENGINE = MergeTree()
ORDER BY (strategy_name, symbol, time)

CREATE TABLE IF NOT EXISTS model_runs (
    run_id UUID DEFAULT generateUUIDv4(),
    trained_at DateTime DEFAULT now(),
    model_name String,
    model_description String,
    s3_key String,
    retrain_interval Float64,
    train_accuracy Float64,
    test_accuracy Float64,
    precision Float64,
    recall Float64,
    f1 Float64               
    ) 
ENGINE = MergeTree()
ORDER BY (trained_at)

CREATE TABLE IF NOT EXISTS portfolio_db_key (
    last_updated DateTime DEFAULT now(),
    cash_balance Float64,
    symbol String,
    quantity Float64,
    market_value Float64,
    portfolio_value Float64,
    strategy_name String,
    strategy_description String
    ) 
ENGINE = ReplacingMergeTree()
ORDER BY (strategy_name, symbol)

CREATE TABLE IF NOT EXISTS portfolio_db_ts (
    time DateTime DEFAULT now(),
    cash_balance Float64,
    symbol String,
    quantity Float64,
    market_value Float64,
    portfolio_value Float64,
    strategy_name String
) 
ENGINE = MergeTree()
ORDER BY (strategy_name, symbol, time)
PRIMARY KEY (strategy_name, symbol)

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

-- stores aggregate states for each symbol and minute
CREATE TABLE minute_bars
(
    minute DateTime,
    symbol String,
    open   AggregateFunction(anyHeavy, Float64),
    high   AggregateFunction(max, Float64),
    low    AggregateFunction(min, Float64),
    close  AggregateFunction(anyLast, Float64),
    avg    AggregateFunction(avg, Float64),
    volume AggregateFunction(sum, Float64)
)
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMMDD(minute)
ORDER BY (symbol, minute)
TTL minute + INTERVAL 9 DAY DELETE;

-- pushes partially aggreate states into minute_bars
CREATE MATERIALIZED VIEW ticks_to_minute
TO minute_bars
AS
SELECT
    toStartOfMinute(timestamp) AS minute,
    symbol,
    anyHeavyState(price) AS open,
    maxState(price)      AS high,
    minState(price)      AS low,
    anyLastState(price)  AS close,
    avgState(price)      AS avg,
    sumState(volume)     AS volume
FROM ticks_db
GROUP BY symbol, minute;

-- minute granular final view
CREATE VIEW minute_bars_final AS
SELECT
    minute,
    symbol,
    anyHeavyMerge(open)   AS open,
    maxMerge(high)        AS high,
    minMerge(low)         AS low,
    anyLastMerge(close)   AS close,
    avgMerge(avg)         AS avg,
    sumMerge(volume)      AS volume
FROM minute_bars
GROUP BY symbol, minute;