
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# 1. PROJECT CONFIGURATION

DATASET_PATH = Path("data/sms+spam+collection/SMSSpamCollection")

print("=" * 55)
print("             SMARTSMS DATASET ANALYSIS")
print("=" * 55)

# 2. LOAD THE DATASET

df = pd.read_csv(
    DATASET_PATH,
    sep="\t",
    header=None,
    names=["label", "message"],
    encoding="latin-1"
)

print("\nDATASET LOADED SUCCESSFULLY!")

# 3. BASIC DATASET INFORMATION

print("\n1. DATASET OVERVIEW")
print("-" * 40)

print("Total messages:", len(df))
print("Number of columns:", len(df.columns))
print("Column names:", list(df.columns))

# 4. CLASS DISTRIBUTION

print("\n2. MESSAGE CLASS DISTRIBUTION")
print("-" * 40)

class_counts = df["label"].value_counts()

for category, count in class_counts.items():
    percentage = (count / len(df)) * 100

    if category == "ham":
        description = "Legitimate messages"
    else:
        description = "Spam messages"

    print(
        f"{description}: {count:,} "
        f"({percentage:.2f}%)"
    )

# 5. CHECK DATA QUALITY

print("\n3. DATA QUALITY CHECK")
print("-" * 40)

print("Missing values:")
print(df.isnull().sum())

print("\nDuplicate messages:", df.duplicated().sum())

print("\nUnique labels:", df["label"].unique())

# 6. DISPLAY SAMPLE MESSAGES

print("\n4. SAMPLE LEGITIMATE MESSAGES")
print("-" * 40)

for message in df[df["label"] == "ham"]["message"].head(3):
    print("-", message)

print("\n5. SAMPLE SPAM MESSAGES")
print("-" * 40)

for message in df[df["label"] == "spam"]["message"].head(3):
    print("-", message)

# 7. VISUALIZE THE DATASET

plt.figure(figsize=(8, 5))

bars = plt.bar(
    ["Legitimate (Ham)", "Spam"],
    [
        class_counts.get("ham", 0),
        class_counts.get("spam", 0)
    ]
)

plt.title("SmartSMS - SMS Dataset Distribution")
plt.xlabel("Message Category")
plt.ylabel("Number of Messages")

for bar in bars:
    height = bar.get_height()

    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{int(height):,}",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

# Save the graph for our presentation
plt.savefig("dataset_distribution.png", dpi=300)

print("\nDataset visualization saved as dataset_distribution.png")

plt.show()

print("\n" + "=" * 55)
print("         DATASET ANALYSIS COMPLETED!")
print("=" * 55)
