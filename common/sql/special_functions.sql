-- initialize balances
TRUNCATE TABLE portfolio_db_key

INSERT INTO portfolio_db_key 
(cash_balance, symbol, quantity, market_value, portfolio_value, strategy_name, strategy_description, status)
VALUES

(200000, 'ETH', 0, 0, 200000, 'Long Only', 'Buy and hold benchmark strategy.', 'closed'),
(200000, 'BTC', 0, 0, 200000, 'Long Only', 'Buy and hold benchmark strategy.', 'closed'),
(200000, 'XRP', 0, 0, 200000, 'Long Only', 'Buy and hold benchmark strategy.', 'closed'),
(200000, 'ADA', 0, 0, 200000, 'Long Only', 'Buy and hold benchmark strategy.', 'closed'),
(200000, 'SOL', 0, 0, 200000, 'Long Only', 'Buy and hold benchmark strategy.', 'closed'),
(200000, 'ETH', 0, 0, 200000, 'Random_Forest', 'Ensemble of decision trees that captures non-linear relationships.', 'closed'),
(200000, 'ETH', 0, 0, 200000, 'Gradient_Boosting', 'Sequentially builds an ensemble to reduce errors and improve accuracy.', 'closed'),
(200000, 'ETH', 0, 0, 200000, 'Logistic_Regression', 'A linear baseline model for classification tasks.', 'closed'),
(200000, 'ETH', 0, 0, 200000, 'LSTM', 'Captures temporal dependencies and sequential patterns in data.', 'closed'),
(200000, 'ETH', 0, 0, 200000, 'SVM', 'Separates classes using non-linear decision boundaries.', 'closed');

-- test
SELECT * FROM portfolio_db_key;

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
