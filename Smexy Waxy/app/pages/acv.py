import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from acv_features import (
    DEFAULT_TEST_DIR,
    DEFAULT_TRAIN_DIR,
    DEFAULT_TRAIN_LABELS,
    discover_workbooks,
    explain_top_pick,
    get_or_train_model,
    load_case,
    score_file,
)

st.set_page_config(page_title="ACV | NebulaX PS3", page_icon="❄️", layout="wide")


@st.cache_resource
def get_model():
    return get_or_train_model()


@st.cache_data
def get_train_labels() -> pd.Series:
    return pd.read_csv(DEFAULT_TRAIN_LABELS, dtype=str).set_index("filename")["faulty_car"]


def score_workbook(path: Path) -> pd.DataFrame:
    return score_file(load_case(path), get_model())


st.title("ACV subsystem — refrigerant-leak locator")
st.write(
    "Upload a train's ACV telemetry workbook (or pick one of the sample cases below) and this "
    "page will point to the car most likely to have a refrigerant leak, in plain language."
)

train_paths = discover_workbooks(DEFAULT_TRAIN_DIR)
test_paths = discover_workbooks(DEFAULT_TEST_DIR)
train_labels = get_train_labels()

source = st.radio(
    "Data source",
    ["Official test case", "Sample training case (answer known)", "Upload a workbook"],
    horizontal=True,
)

workbook_path: Path | None = None
true_car: str | None = None

if source == "Official test case":
    workbook_path = test_paths[0] if test_paths else None
elif source == "Sample training case (answer known)":
    labels_lookup = {p.name: p for p in train_paths}
    chosen_name = st.selectbox("Training case", sorted(labels_lookup))
    workbook_path = labels_lookup[chosen_name]
    true_car = train_labels.get(chosen_name)
else:
    uploaded = st.file_uploader(
        "ACV telemetry workbook (any filename accepted -- content is what's checked)"
    )
    if uploaded is not None:
        tmp_dir = Path(tempfile.mkdtemp())
        workbook_path = tmp_dir / uploaded.name
        workbook_path.write_bytes(uploaded.getvalue())

if workbook_path is None:
    st.info("Choose a sample case or upload a workbook to see a prediction.")
else:
    with st.spinner("Scoring every car against its peers..."):
        ranked = score_workbook(workbook_path)
    top_car = ranked.index[0]
    top = ranked.iloc[0]

    with st.container(border=True):
        st.subheader(f"Most likely fault: Car {top_car}")
        st.progress(min(max(top["probability"], 0.0), 1.0), text=f"Estimated probability: {top['probability']:.0%}")
        st.write(explain_top_pick(ranked))
        if true_car is not None:
            if true_car == top_car:
                st.success(f"Matches the documented answer for this case (Car {true_car}).")
            else:
                st.warning(f"Documented answer for this case is Car {true_car}.")

    st.markdown("#### Full ranking")
    display = ranked.reset_index().rename(columns={
        "car_id": "Car",
        "cooling_gap": "Avg. temp above setpoint while cooling (°C)",
        "z_score": "Peer z-score",
        "probability": "Leak probability",
        "rank": "Rank",
    })
    display["Leak probability"] = display["Leak probability"].map(lambda v: f"{v:.0%}")
    st.dataframe(display.set_index("Rank"), width="stretch")
    st.bar_chart(ranked["probability"], y_label="Leak probability")

    st.download_button(
        "Download this result as CSV",
        pd.DataFrame({"file_id": [workbook_path.name], "ranked_cars": ["|".join(ranked.index)]}).to_csv(index=False),
        file_name="acv_predictions.csv",
        mime="text/csv",
    )

    with st.expander("How this works"):
        st.markdown(
            "- One number per car: how far its cabin temperature sits above its own cooling "
            "setpoint while actively cooling, compared to its 7 peers in the same file. Rows the "
            "file itself flags `Invalid` are excluded first.\n"
            "- That gap is the textbook signature of reduced cooling capacity from a refrigerant "
            "leak; it's converted into a probability by a single-feature logistic regression "
            "trained on the documented leak cases (loaded from a saved model artifact, "
            "`acv_model.joblib`, when present).\n"
            "- One of the six labeled training files uses an entirely different, much richer "
            "column layout the feature can't be computed from, so it's excluded from training "
            "rather than special-cased.\n"
            "- Validated with leave-one-file-out cross-validation across the five usable labeled "
            "files: every one ranks the true faulty car 1st.\n"
            "- Full methodology and validation: [acv_eda.ipynb](../acv_eda.ipynb)."
        )

if st.button("← Back to overview", type="secondary"):
    st.switch_page("app.py")
