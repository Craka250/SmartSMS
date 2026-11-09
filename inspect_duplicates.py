
import pandas as pd
from pathlib import Path

DATASET_PATH = Path("data/sms+spam+collection/SMSSpamCollection")

df = pd.read_csv(
    DATASET_PATH,
    sep="\t",
    header=None,
    names=["label", "message"],
    encoding="latin-1"
)

print("=" * 55)
print("          SMARTSMS DUPLICATE INVESTIGATION")
print("=" * 55)

# 1. Compare loaded rows with physical file lines
with open(DATASET_PATH, "r", encoding="latin-1") as file:
    lines = file.readlines()

print("\n1. FILE INFORMATION")
print("Physical lines:", len(lines))
print("Loaded records:", len(df))
print("Blank physical lines:", sum(not line.strip() for line in lines))

# 2. Exact duplicate records
print("\n2. EXACT DUPLICATE RECORDS")
print("Duplicate rows:", df.duplicated().sum())

# 3. Duplicate message text, regardless of label
print("\n3. DUPLICATE MESSAGE TEXT")
print("Repeated message texts:", df["message"].duplicated().sum())

# 4. Check whether the same message has conflicting labels
label_counts = df.groupby("message")["label"].nunique()
conflicts = label_counts[label_counts > 1]

print("\n4. CONFLICTING LABELS")
print("Messages with multiple labels:", len(conflicts))

if len(conflicts) > 0:
    print("\nExamples:")
    print(
        df[df["message"].isin(conflicts.index)]
        .sort_values("message")
        .head(10)
        .to_string(index=False)
    )

print("\n" + "=" * 55)
print("       DUPLICATE INVESTIGATION COMPLETED")
print("=" * 55)
