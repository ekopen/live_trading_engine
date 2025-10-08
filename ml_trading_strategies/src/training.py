# training.py
# trains all ML models and publishes them to S3 for the trading module

from config import AWS_BUCKET
from setup import s3
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
import pandas as pd
import numpy as np
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
    # normalizing
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    if "LSTM" in name:
        X_train = np.expand_dims(X_train, axis=-1)
        X_test = np.expand_dims(X_test, axis=-1)

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test)
    report = classification_report(y_test, y_pred, digits=3, output_dict=True, zero_division=0)
    precision = report["weighted avg"]["precision"]
    recall = report["weighted avg"]["recall"]
    f1 = report["weighted avg"]["f1-score"]

    logger.info(f"Confusion matrix for {name}: {confusion_matrix(y_test, y_pred)}")
    unique_preds = pd.Series(y_pred).value_counts(normalize=True)
    logger.info(f"Prediction distribution for {name}: {unique_preds.to_dict()}")

    # stores model performance and training history in a clickhouse table
    client.insert('model_runs',
        [(name, description, s3_key, retrain_interval, train_acc, test_acc, precision, recall, f1)],
        column_names=['model_name', 'model_description', 's3_key', 'retrain_interval', 'train_accuracy', 'test_accuracy', 'precision', 'recall', 'f1'])     

    
def upload_to_cloud(key):
    s3.upload_file(key, AWS_BUCKET, key)
    logger.info(f"Upload complete for {key} at s3://{AWS_BUCKET}/{key}")





