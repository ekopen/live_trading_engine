# models.py
# contains all ml related details and constructs classes

from ml_model_template import ML_Model_Template
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from scikeras.wrappers import KerasClassifier
from tensorflow.keras import Input
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import logging
logger = logging.getLogger(__name__)

def build_lstm(input_shape, num_classes=3):
    model = Sequential([
        Input(shape=input_shape),
        LSTM(64, return_sequences=True),
        LSTM(32),
        Dense(32, activation="relu"),
        Dense(num_classes, activation="softmax")
    ])
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model

def build_lstm_model(input_dim=10):
    return build_lstm((input_dim, 1))

def get_ml_models(stop_event):
    logger.info("Getting models.")
    try:
        return [
        ML_Model_Template(
            stop_event=stop_event,
            model_name="Logistic-Regression",
            model_description="A linear baseline model for classification tasks.",
            symbol='ETH',
            model = LogisticRegression(max_iter=500, solver="lbfgs", class_weight="balanced"),
            retrain_interval = 4,
            model_save_type = "pkl"    
        ),
        ML_Model_Template(
            stop_event=stop_event,
            model_name="Gradient-Boosting",
            model_description="Sequentially builds an ensemble to reduce errors and improve accuracy.",
            symbol='ETH',
            model = GradientBoostingClassifier(n_estimators=100, random_state=42),
            retrain_interval = 12,
            model_save_type = "pkl"    
        ),
        ML_Model_Template(
            stop_event=stop_event,
            model_name="Random-Forest",
            model_description="Ensemble of decision trees that captures non-linear relationships.",
            symbol='ETH',
            model = RandomForestClassifier(n_estimators=50, random_state=42, class_weight="balanced"),
            retrain_interval = 6,
            model_save_type = "pkl"    
        ),
        ML_Model_Template(
            stop_event=stop_event,
            model_name="SVM-(RBF-Kernel)",
            model_description="Separates classes using non-linear decision boundaries.",
            symbol='ETH',
            model = SVC(kernel="rbf", C=1.0, probability=True, random_state=42, class_weight="balanced"),
            retrain_interval = 12,
            model_save_type = "pkl"    
        ),
        ML_Model_Template(
            stop_event=stop_event,
            model_name="LSTM",
            model_description="Captures temporal dependencies and sequential patterns in data.",
            symbol='ETH',
            model = KerasClassifier(model=build_lstm_model, epochs=10, batch_size=32, verbose=0),
            retrain_interval = 24,
            model_save_type = "h5"    
        )
        ]
    except Exception as e:
        logger.exception("Error getting models: {e}")