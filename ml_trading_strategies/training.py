# training.py
# trains all ML models and publishes them to S3 for the trading module

from config import AWS_BUCKET
from setup import s3
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd
import logging
logger = logging.getLogger(__name__)

def load_dataset(path):
    df = pd.read_parquet(path)
    feature_cols = [c for c in df.columns if c not in ["price", "future_return", "label","minute"]]
    X = df[feature_cols]
    y = df["label"]
    return X, y

def train_and_eval(X, y, model, name, description, client, s3_key, retrain_interval):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test)
    report = classification_report(y_test, y_pred, digits=3, output_dict=True, zero_division=0)
    precision = report["weighted avg"]["precision"]
    recall = report["weighted avg"]["recall"]
    f1 = report["weighted avg"]["f1-score"]

    # stores model performance and training history in a clickhouse table
    client.insert('model_runs',
        [(name, description, s3_key, retrain_interval, train_acc, test_acc, precision, recall, f1)],
        column_names=['model_name', 'model_description', 's3_key', 'retrain_interval', 'train_accuracy', 'test_accuracy', 'precision', 'recall', 'f1'])     

    
def upload_to_cloud(key):
    s3.upload_file(key, AWS_BUCKET, key)
    logger.info(f"Upload complete for {key} at s3://{AWS_BUCKET}/{key}")





