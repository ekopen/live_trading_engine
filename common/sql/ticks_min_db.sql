-- raw tick table to store incoming tick data
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
TTL toDateTime(timestamp) + INTERVAL 30 DAY DELETE

-- Stores aggregated bar data (1-minute resolution) for each symbol.
-- Each column holds an aggregate function state, allowing rollups and merges.
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
TTL minute + INTERVAL 30 DAY DELETE;

-- Materialized view that aggregates raw tick data into 1-minute bars.
-- The aggregated states are written directly into minute_bars.
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