import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from components.styles import inject_download_button_style
from components.theme import ACCENT_MAP, THEME
from door_features import predict_segments

st.set_page_config(page_title="Door | NebulaX PS3", page_icon="🚪", layout="wide")
inject_download_button_style()

ACCENT = ACCENT_MAP["door"]["color"]


def parse_timestamp(value: str) -> pd.Timestamp:
    year, month, day, hour, minute, second, ms = (int(p) for p in str(value).split("-"))
    return pd.Timestamp(year, month, day, hour, minute, second, ms * 1000)


def with_timing(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["start"] = df["start_time"].map(parse_timestamp)
    df["end"] = df["end_time"].map(parse_timestamp)
    df["duration_s"] = (df["end"] - df["start"]).dt.total_seconds()
    # The raw "2023-7-5-0-0-15-5" timestamps are required for the CSV export but
    # unreadable on screen -- show an ordinary day + time string instead.
    df["start_display"] = df["start"].dt.strftime("%b %d, %H:%M:%S")
    df["end_display"] = df["end"].dt.strftime("%b %d, %H:%M:%S")
    return df


def render_dashboard(df: pd.DataFrame) -> None:
    total = len(df)
    abnormal = int((df["prediction"] == "Abnormal resistance").sum())

    cols = st.columns(4)
    cols[0].metric("Total cycles", total)
    cols[1].metric("Normal", total - abnormal)
    cols[2].metric("Abnormal resistance", abnormal)
    cols[3].metric("Abnormal rate", f"{abnormal / total:.1%}" if total else "—")

    st.markdown("#### Cycle duration over time")
    fig, ax = plt.subplots(figsize=(11, 3))
    colors = df["prediction"].map({"Normal": THEME["success"], "Abnormal resistance": ACCENT})
    x = range(len(df))
    ax.bar(x, df["duration_s"], color=colors)
    ax.set_ylabel("Duration (s)")
    step = max(1, len(df) // 12)
    ticks = list(x)[::step]
    ax.set_xticks(ticks)
    ax.set_xticklabels(df["start_display"].iloc[::step], rotation=30, ha="right", fontsize=8)
    ax.set_title("Each bar is one detected door cycle (red = abnormal resistance)", fontsize=10)
    fig.tight_layout()
    st.pyplot(fig)

    display_columns = {
        "start_display": "start",
        "end_display": "end",
        "prediction": "prediction",
        "duration_s": "duration (s)",
    }

    st.markdown("#### Flagged cycles")
    flagged = df.loc[df["prediction"] == "Abnormal resistance", ["start_display", "end_display", "duration_s"]]
    if len(flagged):
        st.dataframe(
            flagged.rename(columns=display_columns).round({"duration (s)": 2}),
            width="stretch",
        )
    else:
        st.write("No abnormal-resistance cycles detected.")

    with st.expander("All cycles"):
        st.dataframe(
            df[list(display_columns)].rename(columns=display_columns).round({"duration (s)": 2}),
            width="stretch",
        )

    st.download_button(
        "Download predictions.csv",
        df[["start_time", "end_time", "prediction"]].to_csv(index=False),
        file_name="door_predictions.csv",
        mime="text/csv",
    )


st.title("Door subsystem — cycle health")
st.write(
    "Upload a raw door sensor CSV (one row per 20ms sample, with Datetime, "
    "'Motor current(mA)', 'Open command', 'Close command') to detect and classify every "
    "door-open/close cycle."
)

uploaded = st.file_uploader("Raw sensor CSV (any filename accepted -- content is what's checked)")

if uploaded is None:
    st.info("Upload a raw sensor CSV to detect and classify cycles.")
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
                "- Consecutive samples are grouped into door-open/close segments by timestamp "
                "gaps and open/close command changes (or by a `segment_id` column, if the file "
                "already has one).\n"
                "- Each segment's minimum and mean motor current feed a Firth-penalised logistic "
                "regression fitted offline on labeled segments (coefficients reproduced in "
                "`door_features.py`).\n"
                "- A segment is flagged `Abnormal resistance` when the fitted probability clears "
                "a threshold chosen from the labeled data's class gap."
            )

if st.button("← Back to overview", type="secondary"):
    st.switch_page("app.py")
