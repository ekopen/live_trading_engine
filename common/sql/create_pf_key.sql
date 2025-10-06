-- create the table
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