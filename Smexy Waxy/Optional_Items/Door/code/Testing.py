"""
Predict abnormal resistance for each door open/close segment.

HOW TO USE
  1. Put this script and your CSV in the same folder (or use a full path).
  2. Edit INPUT_FILE (and optionally OUTPUT_FILE) in the SETTINGS block below.
  3. Run the script (e.g. press Run in your editor, or `python predict_abnormal.py`).

INPUT : a CSV in the same format as train_split.csv (one row per 20 ms sample;
        needs the columns Datetime, 'Motor current(mA)', 'Open command',
        'Close command'). A 'segment_id' column is used if present; otherwise
        segments are detected automatically.
OUTPUT: a CSV with one row per segment:
        segment_id, operation, start_time, end_time, probability, prediction

MODEL (Firth-penalised logistic regression fitted on train_split + truth):
    logit(P) = -30.297485946 + 0.215139957 * cur_min + 0.038702890 * cur_mean
    cur_min  = minimum Motor current(mA) within the segment
    cur_mean = average Motor current(mA) within the segment
    Prediction = "Abnormal resistance" if P >= THRESHOLD, else "Normal".
"""
import sys

import numpy as np
import pandas as pd

# =============================== SETTINGS ===================================
INPUT_FILE = "Train.csv"      # <-- put your CSV file name / full path here
OUTPUT_FILE = "predictions_split.csv"     # <-- where the results will be saved
THRESHOLD = 0.3887891323108637      # probability cut-off (midpoint of class gap)
# ============================================================================

# ---- fitted model coefficients (do not change unless you refit the model) --
INTERCEPT = -30.297485946310392
B_CUR_MIN = 0.21513995728309812
B_CUR_MEAN = 0.03870289025007016

CURRENT_COL = "Motor current(mA)"
GAP_MS = 500        # samples are 20 ms apart; a bigger gap starts a new segment
LABELS = {1: "Abnormal resistance", 0: "Normal"}


def parse_datetime(s: pd.Series) -> pd.Series:
    """Parse strings like '2023-7-5-0-0-3-700' (Y-M-D-h-m-s-ms)."""
    parts = s.astype(str).str.split("-", expand=True).astype(int)
    parts.columns = ["year", "month", "day", "hour", "minute", "second", "ms"]
    return pd.to_datetime(parts)


def assign_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'op_row' (Open/Close) and 'seg' (segment number) columns."""
    df = df.copy()

    # Operation of each row; rows with neither command inherit a neighbour's.
    op = pd.Series(np.nan, index=df.index, dtype=object)
    op[df["Close command"] == 1] = "Close"
    op[df["Open command"] == 1] = "Open"
    df["op_row"] = op.ffill().bfill()

    if "segment_id" in df.columns:
        df["seg"] = df["segment_id"]
    else:
        ts = parse_datetime(df["Datetime"])
        gap_ms = ts.diff().dt.total_seconds() * 1000
        new_seg = (gap_ms > GAP_MS) | (df["op_row"] != df["op_row"].shift())
        new_seg.iloc[0] = True
        df["seg"] = new_seg.cumsum() - 1
    return df


def main():
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        sys.exit(f"Could not find '{INPUT_FILE}'. Check INPUT_FILE at the top "
                f"of the script (use the full path if the file is elsewhere).")

    needed = ["Datetime", CURRENT_COL, "Open command", "Close command"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        sys.exit(f"Input file is missing required column(s): {missing}")

    df = assign_segments(df)

    rows = []
    for seg, g in df.groupby("seg", sort=False):
        cur_min = g[CURRENT_COL].min()
        cur_mean = g[CURRENT_COL].mean()
        z = INTERCEPT + B_CUR_MIN * cur_min + B_CUR_MEAN * cur_mean
        prob = 1.0 / (1.0 + np.exp(-z))
        rows.append({
            "segment_id": seg,
            "operation": g["op_row"].mode().iloc[0],
            "start_time": g["Datetime"].iloc[0],
            "end_time": g["Datetime"].iloc[-1],
            "probability": round(float(prob), 6),
            "prediction": LABELS[int(prob >= THRESHOLD)],
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_FILE, index=False)

    n_ab = int((out["prediction"] == LABELS[1]).sum())
    print(f"{len(out)} segments -> {n_ab} abnormal, {len(out) - n_ab} normal")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
