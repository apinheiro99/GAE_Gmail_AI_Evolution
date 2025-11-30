import pandas as pd
import joblib
from sklearn.ensemble import VotingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from scipy.sparse import hstack
from xgboost import XGBClassifier


class AISpamClassifier:
    """
    Advanced AI spam classifier using ensemble methods
    Implements continuous learning and model improvement
    """

    def __init__(self, model_path: str = None):
        self.model = None
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.scaler = StandardScaler()
        self.model_path = model_path
        self.training_data = []
        self.training_labels = []

    def initialize_model(self):
        """Initialize ensemble model"""
        self.model = VotingClassifier(
            estimators=[
                ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
                ('svc', SVC(probability=True, random_state=42)),
                ('xgb', XGBClassifier(random_state=42))
            ],
            voting='soft'
        )

    # ============================================================
    # TRAIN
    # ============================================================
    def train(self, features: list, labels: list):
        if not self.model:
            self.initialize_model()

        df = pd.DataFrame(features)

        # Process text
        if 'subject' in df.columns and 'body' in df.columns:
            text_combined = (df['subject'] + " " + df['body']).astype(str).tolist()
            text_matrix = self.vectorizer.fit_transform(text_combined)
        else:
            text_matrix = None

        # Process numerical features
        numerical_features = df.drop(['subject', 'body'], axis=1, errors='ignore')
        numerical_scaled = self.scaler.fit_transform(numerical_features)

        # Combine features
        if text_matrix is not None:
            x_combined = hstack([text_matrix, numerical_scaled])
        else:
            x_combined = numerical_scaled

        # Train model
        self.model.fit(x_combined, labels)

        self.training_data.extend(features)
        self.training_labels.extend(labels)

    # ============================================================
    # PREDICT
    # ============================================================
    def predict(self, email_features: dict) -> dict:
        if not self.model:
            raise ValueError("Model not trained. Call train() first.")

        df = pd.DataFrame([email_features])

        # Text processing
        if 'subject' in df.columns and 'body' in df.columns:
            text_combined = (df['subject'] + " " + df['body']).astype(str).tolist()
            text_matrix = self.vectorizer.transform(text_combined)
        else:
            text_matrix = None

        # Numerical processing
        numerical_features = df.drop(['subject', 'body'], axis=1, errors='ignore')
        numerical_scaled = self.scaler.transform(numerical_features)

        # Combine
        if text_matrix is not None:
            x_combined = hstack([text_matrix, numerical_scaled])
        else:
            x_combined = numerical_scaled

        # Predict
        probabilities = self.model.predict_proba(x_combined)[0]

        return {
            'is_spam': probabilities[1] > 0.5,
            'spam_confidence': float(probabilities[1]),
            'ham_confidence': float(probabilities[0]),
            'risk_level': (
                'high' if probabilities[1] > 0.8
                else 'medium' if probabilities[1] > 0.5
                else 'low'
            )
        }

    # ============================================================
    # SAVE / LOAD MODEL
    # ============================================================
    def save_model(self, path: str):
        joblib.dump({
            'model': self.model,
            'vectorizer': self.vectorizer,
            'scaler': self.scaler
        }, path)

    def load_model(self, path: str):
        loaded = joblib.load(path)
        self.model = loaded['model']
        self.vectorizer = loaded['vectorizer']
        self.scaler = loaded['scaler']
