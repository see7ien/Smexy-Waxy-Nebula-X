import numpy as np
import pandas as pd
import rainflow

from pathlib import Path


# ============================================================
# SETTINGS
# ============================================================

TRAIN_FOLDER = Path("Train")
TEST_FOLDER = Path("Test")
LABEL_FILE = Path("Train_Labels.csv")

EXPONENT = 5.03


# ============================================================
# FATIGUE FEATURE
# ============================================================

def calculate_fatigue(file_path):

    # Read stress time series
    signal = pd.read_csv(
        file_path,
        header=None
    ).iloc[:, 0].values

    # Rainflow counting
    cycles = rainflow.count_cycles(signal)

    # Fatigue proxy:
    # sum(count * stress_range ^ 5.03)
    fatigue = sum(
        count * stress_range ** EXPONENT
        for stress_range, count in cycles
    )

    return fatigue

# ============================================================
# LEARN CONSTANT FROM TRAINING DATA
# ============================================================

labels = pd.read_csv(LABEL_FILE)

ratios = []

print("Processing training files...")

for i, row in labels.iterrows():

    filename = row["filename"]
    actual_damage = row["damage"]

    file_path = TRAIN_FOLDER / filename

    fatigue = calculate_fatigue(file_path)

    # From:
    # damage = C * fatigue
    #
    # therefore:
    # C = damage / fatigue

    ratio = actual_damage / fatigue

    ratios.append(ratio)

    print(
        f"Train {i + 1}/{len(labels)}: "
        f"{filename}"
    )


# Learn C using all 64 training files
C = np.mean(ratios)

print("\nLearned constant C:")
print(C)

# ============================================================
# PREDICT TEST DATA
# ============================================================

test_files = sorted(
    TEST_FOLDER.glob("*.csv")
)

predictions = []

print("\nProcessing test files...")

for i, file_path in enumerate(test_files):

    fatigue = calculate_fatigue(file_path)

    predicted_damage = C * fatigue

    predictions.append({
        "file_id": file_path.name,
        "prediction": predicted_damage
    })

    print(
        f"Test {i + 1}/{len(test_files)}: "
        f"{file_path.name} -> "
        f"{predicted_damage:.8f}"
    )

# ============================================================
# SAVE PREDICTIONS
# ============================================================

submission = pd.DataFrame(predictions)

submission.to_csv(
    "shm_predictions.csv",
    index=False
)

print("\n==============================")
print("DONE")
print("==============================")

print(submission)

print("\nSaved to predictions.csv")
