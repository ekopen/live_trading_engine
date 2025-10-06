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


-- backfill
INSERT INTO minute_bars
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
