from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from components.theme import ACCENT_MAP, THEME
from door_features import predict_segments

st.set_page_config(page_title="Door | NebulaX PS3", page_icon="🚪", layout="wide")

ACCENT = ACCENT_MAP["door"]["color"]
SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "Door" / "sample_door_predictions.csv"


def parse_timestamp(value: str) -> pd.Timestamp:
    year, month, day, hour, minute, second, ms = (int(p) for p in str(value).split("-"))
    return pd.Timestamp(year, month, day, hour, minute, second, ms * 1000)


def with_timing(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["start"] = df["start_time"].map(parse_timestamp)
    df["end"] = df["end_time"].map(parse_timestamp)
    df["duration_s"] = (df["end"] - df["start"]).dt.total_seconds()
    return df


def render_dashboard(df: pd.DataFrame) -> None:
    total = len(df)
    abnormal = int((df["prediction"] == "Abnormal resistance").sum())

    cols = st.columns(4)
    cols[0].metric("Total cycles", total)
    cols[1].metric("Normal", total - abnormal)
    cols[2].metric("Abnormal resistance", abnormal)
    cols[3].metric("Abnormal rate", f"{abnormal / total:.1%}" if total else "—")

    st.markdown("#### Cycle timeline")
    fig, ax = plt.subplots(figsize=(11, 2))
    colors = df["prediction"].map({"Normal": THEME["success"], "Abnormal resistance": ACCENT})
    ax.scatter(df["start"], [0] * len(df), c=colors, s=80, marker="|", linewidths=3)
    ax.set_yticks([])
    ax.set_xlabel("Time")
    ax.set_title("Each mark is one detected door cycle (red = abnormal resistance)", fontsize=10)
    fig.tight_layout()
    st.pyplot(fig)

    st.markdown("#### Flagged cycles")
    flagged = df.loc[df["prediction"] == "Abnormal resistance", ["start_time", "end_time", "duration_s"]]
    if len(flagged):
        st.dataframe(flagged.rename(columns={"duration_s": "duration (s)"}), width="stretch")
    else:
        st.write("No abnormal-resistance cycles detected.")

    with st.expander("All cycles"):
        st.dataframe(
            df[["start_time", "end_time", "prediction", "duration_s"]].rename(columns={"duration_s": "duration (s)"}),
            width="stretch",
        )

    st.download_button(
        "Download this result as CSV",
        df[["start_time", "end_time", "prediction"]].to_csv(index=False),
        file_name="door_predictions.csv",
        mime="text/csv",
    )


st.title("Door subsystem — cycle health")
st.write(
    "Upload raw door sensor data to detect and classify each open/close cycle, or browse "
    "pre-computed sample results."
)

source = st.radio(
    "Data source",
    ["Live prediction (upload raw sensor data)", "Sample predictions", "Upload a predictions CSV"],
    horizontal=True,
)

if source == "Sample predictions":
    render_dashboard(with_timing(pd.read_csv(SAMPLE_PATH)))
elif source == "Upload a predictions CSV":
    uploaded = st.file_uploader("Predictions file (any filename accepted -- content is what's checked)")
    if uploaded is None:
        st.info("Upload a predictions CSV to see the dashboard.")
    else:
        try:
            df = with_timing(pd.read_csv(uploaded))
        except KeyError as exc:
            st.error(
                f"This doesn't look like a door_predictions.csv -- missing column {exc}. "
                "Expected start_time, end_time, prediction. Raw sensor data goes in "
                "\"Live prediction\" instead."
            )
        else:
            render_dashboard(df)
else:
    uploaded = st.file_uploader("Raw sensor CSV (any filename accepted -- content is what's checked)")
    if uploaded is None:
        st.info(
            "Upload a raw sensor CSV (one row per 20ms sample, with Datetime, "
            "'Motor current(mA)', 'Open command', 'Close command') to detect and classify cycles."
        )
    else:
        try:
            with st.spinner("Detecting door cycles and scoring each one..."):
                segments = predict_segments(pd.read_csv(uploaded))
        except ValueError as exc:
            st.error(f"Couldn't read this as raw door sensor data ({exc}).")
        else:
            render_dashboard(with_timing(segments))

            with st.expander("How this works"):
                st.markdown(
                    "- Consecutive samples are grouped into door-open/close segments by "
                    "timestamp gaps and open/close command changes (or by a `segment_id` "
                    "column, if the file already has one).\n"
                    "- Each segment's minimum and mean motor current feed a Firth-penalised "
                    "logistic regression fitted offline on labeled segments "
                    "(coefficients reproduced in `door_features.py` from `models/door_model.py`).\n"
                    "- A segment is flagged `Abnormal resistance` when the fitted probability "
                    "clears a threshold chosen from the labeled data's class gap."
                )

if st.button("← Back to overview", type="secondary"):
    st.switch_page("app.py")
