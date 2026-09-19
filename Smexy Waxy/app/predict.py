"""Generate ACV car rankings from one workbook or a directory of workbooks.

Uses the saved model (acv_model.joblib) if present, otherwise retrains the
single-feature logistic regression from the bundled labeled training cases
(data/ACV/ACV/Train + Train_Labels.csv). See acv_features.py and
acv_eda.ipynb for the modeling rationale.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from acv_features import (
    discover_workbooks,
    format_predictions,
    get_or_train_model,
    load_case,
    score_file,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Workbook or directory containing .xlsx files")
    parser.add_argument("--output", required=True, type=Path, help="Output CSV path")
    args = parser.parse_args()

    paths = [args.input] if args.input.is_file() else discover_workbooks(args.input)
    if not paths:
        raise FileNotFoundError(f"No .xlsx workbooks found under {args.input}")

    model = get_or_train_model()
    scored_by_file = {path.name: score_file(load_case(path), model) for path in paths}
    predictions = format_predictions(scored_by_file)

    expected_files = {path.name for path in paths}
    if set(predictions["file_id"]) != expected_files:
        raise ValueError("Prediction output does not contain exactly one row per input workbook")
    if predictions["ranked_cars"].str.split("|").map(len).eq(0).any():
        raise ValueError("At least one workbook produced an empty car ranking")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(args.output, index=False)
    print(predictions.to_string(index=False))


if __name__ == "__main__":
    main()
