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

-- initialize balances
INSERT INTO portfolio_db_key 
(cash_balance, symbol, quantity, market_value, portfolio_value, strategy_name, strategy_description)
VALUES

(200000, 'ETH', 0, 0, 200000, 'Long Only', 'Buy and hold benchmark strategy.'),
(200000, 'BTC', 0, 0, 200000, 'Long Only', 'Buy and hold benchmark strategy.'),
(200000, 'XRP', 0, 0, 200000, 'Long Only', 'Buy and hold benchmark strategy.'),
(200000, 'ADA', 0, 0, 200000, 'Long Only', 'Buy and hold benchmark strategy.'),
(200000, 'SOL', 0, 0, 200000, 'Long Only', 'Buy and hold benchmark strategy.'),
(200000, 'ETH', 0, 0, 200000, 'Random_Forest', 'Ensemble of decision trees that captures non-linear relationships.'),
(200000, 'ETH', 0, 0, 200000, 'Gradient_Boosting', 'Sequentially builds an ensemble to reduce errors and improve accuracy.'),
(200000, 'ETH', 0, 0, 200000, 'Logistic_Regression', 'A linear baseline model for classification tasks.'),
(200000, 'ETH', 0, 0, 200000, 'LSTM', 'Captures temporal dependencies and sequential patterns in data.'),
(200000, 'ETH', 0, 0, 200000, 'SVM', 'Separates classes using non-linear decision boundaries.');
