# feature.py
# creates updated feature tables for training
import logging
logger = logging.getLogger(__name__)

# this will have access to about a weeks worth of data
# should yield ~ 10k rows to train on
def get_data(client, symbol): 
    df = client.query_df(f"""
        SELECT minute, open as price
        FROM minute_bars_final
        WHERE symbol = '{symbol}'
        ORDER BY minute ASC                             
    """)
    return df

def build_features(df):
    # standard features
    df["returns"] = df["price"].pct_change()
    df["sma_30"] = df["price"].rolling(window=30).mean()
    df["sma_60"] = df["price"].rolling(window=60).mean()
    df["momentum_10"] = df["price"] / df["price"].shift(10) - 1
    df["momentum_30"] = df["price"] / df["price"].shift(30) - 1
    df["volatility_30"] = df["returns"].rolling(window=30).std()
    for lag in [1, 2, 5]:
        df[f"lag_return_{lag}"] = df["returns"].shift(lag)

    # RSI
    delta = df["price"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["rsi_14"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["price"].ewm(span=12, adjust=False).mean()
    ema26 = df["price"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    # STATIONARY FEATURES
    df["price_change"] = df["price"].diff()
    df["sma_ratio"] = df["sma_30"] / df["sma_60"] - 1
    df["macd_diff"] = df["macd"] - df["macd_signal"]

    # Smoothed return signal
    df["ema_return_10"] = df["returns"].ewm(span=10, adjust=False).mean()

    # Rolling z-score of returns
    df["zscore_30"] = (df["returns"] - df["returns"].rolling(30).mean()) / df["returns"].rolling(30).std()

    # Directional signal (momentum vs volatility)
    df["dir_strength"] = df["momentum_10"] / (df["volatility_30"] + 1e-8)
        
    df = df.dropna()
    return df

def create_labels(df, horizon, buy_q, sell_q):
    df = df.copy() 
    df["future_return"] = df["price"].shift(-horizon) / df["price"] - 1
    df["future_return"] = df["future_return"].ewm(span=5, adjust=False).mean()

    # compute dynamic thresholds
    upper = df["future_return"].quantile(buy_q)
    lower = df["future_return"].quantile(sell_q)

    df["label"] = 1  # HOLD by default
    df.loc[df["future_return"] > upper, "label"] = 2  # BUY
    df.loc[df["future_return"] < lower, "label"] = 0  # SELL

    # Ensure minimum class ratios
    min_class_ratio = 0.1
    counts = df["label"].value_counts(normalize=True)
    if counts.get(2, 0) < min_class_ratio or counts.get(0, 0) < min_class_ratio:
        logger.warning(f"Imbalanced labels detected (BUY={counts.get(2,0):.3f}, SELL={counts.get(0,0):.3f}). Expanding quantile thresholds.")
        buy_q = min(0.95, buy_q + 0.05)
        sell_q = max(0.05, sell_q - 0.05)
        upper = df["future_return"].quantile(buy_q)
        lower = df["future_return"].quantile(sell_q)
        df.loc[df["future_return"] > upper, "label"] = 2
        df.loc[df["future_return"] < lower, "label"] = 0

    df = df.dropna()
    counts = df["label"].value_counts(normalize=True).sort_index()
    return df, counts