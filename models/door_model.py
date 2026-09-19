import sys

import numpy as np
import pandas as pd

INPUT_FILE = "../02_Datasets/Door/Test.csv"
OUTPUT_FILE = "door_predictions.csv"
THRESHOLD = 0.3887891323108637    # probability threshold determined from 88 randomly selected train segments

#model coefficients found from 88 randomly selected train segments
INTERCEPT = -30.297485946310392
B_CUR_MIN = 0.21513995728309812
B_CUR_MEAN = 0.03870289025007016

CURRENT_COL = "Motor current(mA)"
GAP_MS = 500        # samples are 20 ms apart so a bigger gap starts a new segment
LABELS = {1: "Abnormal resistance", 0: "Normal"}


def parse_datetime(s: pd.Series) -> pd.Series:
    """Parse strings like '2023-7-5-0-0-3-700' (Y-M-D-h-m-s-ms)."""
    parts = s.astype(str).str.split("-", expand=True).astype(int)
    parts.columns = ["year", "month", "day", "hour", "minute", "second", "ms"]
    return pd.to_datetime(parts)


def assign_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'op_row' (Open/Close) and 'seg' (segment number) columns."""
    df = df.copy()
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
    out[["start_time", "end_time", "prediction"]].to_csv(OUTPUT_FILE, index=False)

    n_ab = int((out["prediction"] == LABELS[1]).sum())
    print(f"{len(out)} segments -> {n_ab} abnormal, {len(out) - n_ab} normal")
    print(f"Saved to {OUTPUT_FILE}")

main()