"""ACV refrigerant-leak scoring: the shared logic behind predict.py and the Streamlit app.

The single engineered feature, why it was chosen, and the model's own
validation (leave-one-file-out, rank-decay score) live in `acv_eda.ipynb` --
that notebook is the source of truth for *why* this is the approach. This
module is its thin, reusable twin: build the same feature, score it with the
same fitted model, format the same output. There is no import in either
direction between the two, so keeping them in sync is a manual discipline
(mirror any change here into the notebook, and vice versa) rather than
something enforced automatically.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

RUNNING_MODE_PARAM = "ACV Running Mode"
ACTUAL_TEMP_PARAM = "Indoor Average Temperature"
TARGET_TEMP_PARAM = "ACV Control Temperature (Cooling)"
INFO_VALID_PARAM = "ACV Information Valid"
ACTIVE_MODES = {"Automatic Cooling", "Full Cooling"}

DATASET_ROOT = Path(__file__).parent / "data" / "ACV" / "ACV"
DEFAULT_TRAIN_DIR = DATASET_ROOT / "Train"
DEFAULT_TRAIN_LABELS = DATASET_ROOT / "Train_Labels.csv"
DEFAULT_TEST_DIR = DATASET_ROOT / "Test"

# acv_case_04.xlsx uses a much richer, differently-named parameter set (see
# acv_eda.ipynb section 2) -- the feature below can't be computed from it, so
# it's excluded from training rather than special-cased.
EXCLUDED_TRAINING_FILES = {"acv_case_04.xlsx"}

MODEL_PATH = Path(__file__).parent / "acv_model.joblib"


def discover_workbooks(input_dir: str | Path) -> list[Path]:
    """Return workbook paths in deterministic order."""
    return sorted(Path(input_dir).glob("*.xlsx"))


def car_ids_of(df: pd.DataFrame) -> list[str]:
    """Car IDs from "Car 01 - <parameter>" columns, excluding the "Car model" metadata column."""
    ids = set()
    for column in df.columns:
        if column.startswith("Car ") and " - " in column:
            number = column.split(" - ")[0][4:]
            if number.isdigit():
                ids.add(number)
    return sorted(ids)


def load_case(path: str | Path) -> pd.DataFrame:
    """Read one workbook, parse and sort by Time, and verify there are no duplicate columns."""
    df = pd.read_excel(path, engine="openpyxl")
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
    df = df.sort_values("Time").reset_index(drop=True)
    assert not df.columns.duplicated().any(), f"{path} has duplicate columns"
    return df


def cooling_gap(df: pd.DataFrame, car: str) -> float:
    """Mean(actual - target temperature) while the car is actively cooling.

    Positive means the cabin ran warmer than its own setpoint while the unit
    was trying to cool it -- the signature of reduced cooling capacity from a
    refrigerant leak. Rows the file itself flags Invalid are excluded. NaN if
    this file doesn't carry these exact columns for this car.
    """
    mode_col = f"Car {car} - {RUNNING_MODE_PARAM}"
    valid_col = f"Car {car} - {INFO_VALID_PARAM}"
    actual_col = f"Car {car} - {ACTUAL_TEMP_PARAM}"
    target_col = f"Car {car} - {TARGET_TEMP_PARAM}"
    if not all(column in df.columns for column in (mode_col, valid_col, actual_col, target_col)):
        return np.nan

    active = df[mode_col].isin(ACTIVE_MODES) & (df[valid_col] != "Invalid")
    actual = pd.to_numeric(df[actual_col], errors="coerce")
    target = pd.to_numeric(df[target_col], errors="coerce")
    gap = (actual - target)[active]
    return float(gap.mean()) if gap.notna().any() else np.nan


def peer_zscore(values: pd.Series) -> pd.Series:
    """Robust (median/MAD) z-score of a car's feature against the other cars in the same file."""
    median = values.median()
    mad = (values - median).abs().median()
    scale = mad if mad > 0 else (values.std() if values.std() > 0 else 1.0)
    return (values - median) / scale


def score_file(df: pd.DataFrame, model: LogisticRegression) -> pd.DataFrame:
    """One row per car (indexed by car_id): cooling_gap, z_score, probability, rank."""
    gaps = pd.Series({car: cooling_gap(df, car) for car in car_ids_of(df)})
    z = peer_zscore(gaps)
    probability = model.predict_proba(z.to_frame("z"))[:, 1]
    result = pd.DataFrame({"cooling_gap": gaps, "z_score": z, "probability": probability})
    result = result.sort_values("probability", ascending=False)
    result["rank"] = range(1, len(result) + 1)
    result.index.name = "car_id"
    return result


def rank_decay_score(ranked_car_ids: list[str], true_car: str) -> float:
    """The competition's scoring formula: (n - (r - 1)) / n for true car at rank r of n."""
    n = len(ranked_car_ids)
    if true_car not in ranked_car_ids:
        return 0.0
    r = ranked_car_ids.index(true_car) + 1
    return (n - (r - 1)) / n


def training_table(
    train_dir: str | Path = DEFAULT_TRAIN_DIR,
    labels_path: str | Path = DEFAULT_TRAIN_LABELS,
) -> pd.DataFrame:
    """One row per car per evaluable training file: file_id, car_id, z, is_faulty."""
    labels = pd.read_csv(labels_path, dtype=str).set_index("filename")["faulty_car"]
    rows = []
    for path in discover_workbooks(train_dir):
        if path.name in EXCLUDED_TRAINING_FILES:
            continue
        df = load_case(path)
        gaps = pd.Series({car: cooling_gap(df, car) for car in car_ids_of(df)})
        z = peer_zscore(gaps)
        true_car = labels[path.name]
        for car, value in z.items():
            rows.append({"file_id": path.name, "car_id": car, "z": value, "is_faulty": int(car == true_car)})
    return pd.DataFrame(rows)


def train_fault_classifier(table: pd.DataFrame) -> LogisticRegression:
    """Fit the single-feature logistic regression that turns z-scores into probabilities."""
    return LogisticRegression(class_weight="balanced").fit(table[["z"]], table["is_faulty"])


def save_model(model: LogisticRegression, path: str | Path = MODEL_PATH) -> None:
    joblib.dump(model, path)


def load_model(path: str | Path = MODEL_PATH) -> LogisticRegression | None:
    """Load the saved artifact if one exists; None means "not trained/saved yet"."""
    path = Path(path)
    return joblib.load(path) if path.exists() else None


def get_or_train_model() -> LogisticRegression:
    """The saved artifact if present, otherwise a fresh fit from the bundled training data."""
    model = load_model()
    if model is not None:
        return model
    return train_fault_classifier(training_table())


def explain_top_pick(scored: pd.DataFrame) -> str:
    """One plain-language sentence justifying the top-ranked car for one file."""
    scored = scored.sort_values("rank")
    top_car = scored.index[0]
    top = scored.iloc[0]
    runner_up = scored["cooling_gap"].iloc[1:].max() if len(scored) > 1 else float("nan")
    return (
        f"Car {top_car} stayed {top['cooling_gap']:.2f}°C above its own cooling setpoint "
        f"while actively cooling — the largest gap of all {len(scored)} cars in this file "
        f"(next-highest: {runner_up:.2f}°C). "
        f"Estimated probability this is the car with the refrigerant leak: {top['probability']:.0%}."
    )


def format_predictions(scored_by_file: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for file_id in sorted(scored_by_file):
        ranked_ids = scored_by_file[file_id].sort_values("rank").index.tolist()
        rows.append({"file_id": file_id, "ranked_cars": "|".join(ranked_ids)})
    return pd.DataFrame(rows, columns=["file_id", "ranked_cars"])
