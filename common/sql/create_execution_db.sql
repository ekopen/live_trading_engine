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