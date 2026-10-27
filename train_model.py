import os
import warnings

import joblib
import pandas as pd
from bs4 import MarkupResemblesLocatorWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from utils.preprocessing import clean_text

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
tqdm.pandas()

DATASET_PATH = "dataset/email_dataset_classification.csv"
CLEAN_CACHE = "dataset/cleaned_cache.csv"
MODEL_DIR = "model"
SAMPLE_SIZE = None  # test ke liye 20000 likho, full training ke liye None

# 1. Load / clean
if os.path.exists(CLEAN_CACHE):
    print("Cached cleaned data mil gaya, load kar raha hoon...")
    df = pd.read_csv(CLEAN_CACHE)
else:
    print("Loading Dataset...")
    df = pd.read_csv(DATASET_PATH)
    print("Dataset Loaded Successfully")

    print("\nMissing Values Before Cleaning:\n")
    print(df.isnull().sum())

    df = df.dropna(subset=["message", "label"]).copy()
    df["message"] = df["message"].astype(str)

    if SAMPLE_SIZE and len(df) > SAMPLE_SIZE:
        df = df.sample(SAMPLE_SIZE, random_state=42)

    print("\nCleaning text (time lag sakta hai, Ctrl+C mat dabana)...")
    df["clean_message"] = df["message"].progress_apply(clean_text)

    if SAMPLE_SIZE is None:
        df.to_csv(CLEAN_CACHE, index=False)

df["clean_message"] = df["clean_message"].fillna("").astype(str)
df = df[df["clean_message"].str.strip() != ""]

# 2. Labels ko 0/1 mein convert karo
if df["label"].dtype == object:
    df["label"] = (
        df["label"].astype(str).str.strip().str.lower()
        .map({"spam": 1, "ham": 0, "not spam": 0, "1": 1, "0": 0})
    )
    df = df.dropna(subset=["label"])
df["label"] = df["label"].astype(int)

print("\nLabel counts:\n", df["label"].value_counts())

# 3. Split
X_train, X_test, y_train, y_test = train_test_split(
    df["clean_message"], df["label"],
    test_size=0.2, random_state=42, stratify=df["label"],
)

# 4. TF-IDF
print("\nTF-IDF bana raha hoon...")
vectorizer = TfidfVectorizer(max_features=50000, ngram_range=(1, 2), min_df=2)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# 5. Train
print("Model train ho raha hai...")
model = LogisticRegression(max_iter=1000, class_weight="balanced")
model.fit(X_train_vec, y_train)

# 6. Evaluate
pred = model.predict(X_test_vec)
print("\nAccuracy:", round(accuracy_score(y_test, pred), 4))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, pred))
print("\nClassification Report:\n", classification_report(y_test, pred))

# 7. Save
os.makedirs(MODEL_DIR, exist_ok=True)
joblib.dump(model, os.path.join(MODEL_DIR, "spam_model.pkl"))
# predict.py jo naam use kare wahi chalega, isliye dono naam se save:
joblib.dump(vectorizer, os.path.join(MODEL_DIR, "vectorizer.pkl"))
joblib.dump(vectorizer, os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"))

print("\nModel aur vectorizer save ho gaye:", MODEL_DIR)