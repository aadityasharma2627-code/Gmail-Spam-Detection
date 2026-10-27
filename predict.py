import joblib
from utils.preprocessing import clean_text

# Load trained model
model = joblib.load("model/spam_model.pkl")

# Load vectorizer
vectorizer = joblib.load("model/tfidf_vectorizer.pkl")


def predict_email(subject, body):
    """
    Predict whether an email is Spam or Ham.
    """

    # Combine subject and body
    email = f"{subject} {body}"

    # Clean text
    email = clean_text(email)

    # Vectorize
    vector = vectorizer.transform([email])

    # Prediction
    prediction = model.predict(vector)[0]

    # Probability (if supported)
    confidence = None

    if hasattr(model, "predict_proba"):
        confidence = model.predict_proba(vector).max() * 100

    return prediction, confidence