"""Door abnormal-resistance segment classifier.

Model: a Firth-penalised logistic regression fitted offline on labeled door
open/close segments, using each segment's minimum and mean motor current.
The fitted coefficients are reproduced here from `Testing.py` (kept in the
repo as the original reference/derivation script) rather than re-fit at
runtime -- there's no raw labeled training data bundled in this app.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

INTERCEPT = -30.297485946310392
B_CUR_MIN = 0.21513995728309812
B_CUR_MEAN = 0.03870289025007016
THRESHOLD = 0.3887891323108637

CURRENT_COL = "Motor current(mA)"
GAP_MS = 500  # samples are 20ms apart; a bigger gap starts a new segment
LABELS = {1: "Abnormal resistance", 0: "Normal"}
REQUIRED_COLUMNS = ["Datetime", CURRENT_COL, "Open command", "Close command"]


def parse_datetime(series: pd.Series) -> pd.Series:
    """Parse strings like '2023-7-5-0-0-3-700' (Y-M-D-h-m-s-ms)."""
    parts = series.astype(str).str.split("-", expand=True).astype(int)
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


def predict_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Raw sensor rows in, one row per detected door-open/close segment out."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"missing required column(s): {', '.join(missing)}")

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
    return pd.DataFrame(rows)
