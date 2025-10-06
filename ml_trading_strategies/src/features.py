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
    
    df = df.dropna()
    return df

def create_labels(df, horizon, buy_q, sell_q):
    df = df.copy()  # make sure it's not a view
    df["future_return"] = df["price"].shift(-horizon) / df["price"] - 1
    # compute dynamic thresholds
    upper = df["future_return"].quantile(buy_q)
    lower = df["future_return"].quantile(sell_q)

    df["label"] = 1  # HOLD by default
    df.loc[df["future_return"] > upper, "label"] = 2  # BUY
    df.loc[df["future_return"] < lower, "label"] = 0  # SELL

    df = df.dropna()
    counts = df["label"].value_counts(normalize=True).sort_index()
    return df, counts