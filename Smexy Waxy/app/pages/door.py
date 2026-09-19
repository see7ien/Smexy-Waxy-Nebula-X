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


def render_abnormal_pie(ax, sub_df: pd.DataFrame, label: str) -> None:
    abnormal = int((sub_df["prediction"] == "Abnormal resistance").sum())
    normal = len(sub_df) - abnormal
    ax.pie(
        [normal, abnormal],
        labels=["Normal", "Abnormal"],
        colors=[THEME["success"], ACCENT],
        autopct="%1.0f%%",
        startangle=90,
    )
    ax.set_title(f"{label} (n={len(sub_df)})")


def render_dashboard(df: pd.DataFrame) -> None:
    total = len(df)
    abnormal = int((df["prediction"] == "Abnormal resistance").sum())

    cols = st.columns(4)
    cols[0].metric("Total segments", total)
    cols[1].metric("Normal", total - abnormal)
    cols[2].metric("Abnormal resistance", abnormal)
    cols[3].metric("Abnormal rate", f"{abnormal / total:.1%}" if total else "—")

    st.markdown("#### Abnormal rate by operation")
    operations = sorted(df["operation"].dropna().unique())
    if len(operations) >= 2:
        pie_cols = st.columns(len(operations))
        for col, op in zip(pie_cols, operations):
            fig, ax = plt.subplots(figsize=(4, 4))
            render_abnormal_pie(ax, df[df["operation"] == op], op)
            col.pyplot(fig)
    elif len(operations) == 1:
        fig, ax = plt.subplots(figsize=(4, 4))
        render_abnormal_pie(ax, df[df["operation"] == operations[0]], operations[0])
        st.pyplot(fig)
    else:
        st.write("No operation data available to break down.")

    display_columns = {
        "start_display": "start",
        "end_display": "end",
        "duration_s": "duration (s)",
    }

    abnormal_df = df.loc[df["prediction"] == "Abnormal resistance", list(display_columns)]
    normal_df = df.loc[df["prediction"] == "Normal", list(display_columns)]

    with st.expander(f"Abnormal segments ({len(abnormal_df)})"):
        if len(abnormal_df):
            st.dataframe(abnormal_df.rename(columns=display_columns).round({"duration (s)": 2}), width="stretch")
        else:
            st.write("No abnormal-resistance segments detected.")

    with st.expander(f"Normal segments ({len(normal_df)})"):
        st.dataframe(normal_df.rename(columns=display_columns).round({"duration (s)": 2}), width="stretch")

    st.download_button(
        "Download predictions.csv",
        df[["start_time", "end_time", "prediction"]].to_csv(index=False),
        file_name="door_predictions.csv",
        mime="text/csv",
    )


st.title("Door subsystem — segment health")
st.write(
    "Upload a raw door sensor CSV (one row per 20ms sample, with Datetime, "
    "'Motor current(mA)', 'Open command', 'Close command') to detect and classify every "
    "door-open/close segment."
)

uploaded = st.file_uploader("Raw sensor CSV (any filename accepted -- content is what's checked)")

if uploaded is None:
    st.info("Upload a raw sensor CSV to detect and classify segments.")
else:
    try:
        with st.spinner("Detecting door segments and scoring each one..."):
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
