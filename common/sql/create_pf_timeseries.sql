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