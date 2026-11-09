
import csv
import pandas as pd
import matplotlib.pyplot as plt
import joblib

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)

# ==========================================
# 1. PROJECT CONFIGURATION
# ==========================================

DATASET_PATH = Path("data/sms+spam+collection/SMSSpamCollection")

MODEL_PATH = Path("sms_spam_model.pkl")

print("=" * 60)
print("             SMARTSMS MODEL TRAINING")
print("=" * 60)

# ==========================================
# 2. VERIFY DATASET RECORDS
# ==========================================

with open(DATASET_PATH, "r", encoding="latin-1", newline="") as file:
    csv_records = list(csv.reader(file, delimiter="\t"))

print("\n1. DATASET VERIFICATION")
print("-" * 45)

print("Logical records found by CSV reader:", len(csv_records))

# ==========================================
# 3. LOAD AND PREPARE DATA
# ==========================================

df = pd.read_csv(
    DATASET_PATH,
    sep="\t",
    header=None,
    names=["label", "message"],
    encoding="latin-1"
)

print("\n2. DATA PREPARATION")
print("-" * 45)

print("Original records:", len(df))

# Check for messages assigned conflicting labels
conflicting_labels = (
    df.groupby("message")["label"].nunique()
)

conflicting_labels = conflicting_labels[
    conflicting_labels > 1
]

if len(conflicting_labels) > 0:
    raise ValueError(
        "Some messages have conflicting labels. "
        "Resolve them before training."
    )

# Remove repeated message texts
df = df.drop_duplicates(
    subset=["message"],
    keep="first"
).copy()

print("Records after removing duplicates:", len(df))
print("Duplicates removed:", 5572 - len(df))

print("\nClass distribution after preparation:")
print(df["label"].value_counts())

# ==========================================
# 4. SEPARATE FEATURES AND TARGET
# ==========================================

X = df["message"]
y = df["label"]

# X = SMS messages
# y = their correct categories (ham or spam)

# ==========================================
# 5. SPLIT TRAINING AND TESTING DATA
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\n3. TRAINING AND TESTING SPLIT")
print("-" * 45)

print("Training messages:", len(X_train))
print("Testing messages:", len(X_test))

# ==========================================
# 6. BUILD MACHINE-LEARNING PIPELINE
# ==========================================

model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            min_df=2
        )
    ),
    (
        "classifier",
        MultinomialNB()
    )
])

# ==========================================
# 7. TRAIN THE MODEL
# ==========================================

print("\n4. MODEL TRAINING")
print("-" * 45)

print("Training SmartSMS model...")

model.fit(X_train, y_train)

print("MODEL TRAINING COMPLETED SUCCESSFULLY!")

# ==========================================
# 8. MAKE TEST PREDICTIONS
# ==========================================

y_pred = model.predict(X_test)

# ==========================================
# 9. EVALUATE MODEL PERFORMANCE
# ==========================================

print("\n5. MODEL EVALUATION")
print("-" * 45)

accuracy = accuracy_score(y_test, y_pred)

print(f"Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        y_pred,
        labels=["ham", "spam"],
        target_names=["Legitimate (Ham)", "Spam"],
        zero_division=0
    )
)

# ==========================================
# 10. CONFUSION MATRIX
# ==========================================

cm = confusion_matrix(
    y_test,
    y_pred,
    labels=["ham", "spam"]
)

print("\nConfusion Matrix:")
print(cm)

display = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=["Legitimate", "Spam"]
)

display.plot(values_format="d")

plt.title("SmartSMS - Confusion Matrix")
plt.tight_layout()

plt.savefig(
    "confusion_matrix.png",
    dpi=300
)

print("\nConfusion matrix saved as confusion_matrix.png")

plt.show()

# ==========================================
# 11. SAVE TRAINED MODEL
# ==========================================

joblib.dump(model, MODEL_PATH)

print("\n6. MODEL SAVED")
print("-" * 45)

print("Saved model:", MODEL_PATH)

# ==========================================
# 12. COMPLETION
# ==========================================

print("\n" + "=" * 60)
print("       SMARTSMS TRAINING COMPLETED!")
print("=" * 60)
