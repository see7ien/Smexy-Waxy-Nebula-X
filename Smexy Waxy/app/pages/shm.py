import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from components.theme import ACCENT_MAP
from shm_features import predict_damage

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "SHM" / "sample_shm_predictions.csv"
ACCENT = ACCENT_MAP["shm"]["color"]
HISTORY_LENGTH = 5

st.set_page_config(page_title="SHM | NebulaX PS3", page_icon="📡", layout="wide")


def load_sample() -> pd.DataFrame:
    df = pd.read_csv(SAMPLE_PATH)
    # This dataset's own output uses filename/damage; the spec's column names are
    # file_id/prediction. Accept either without treating it as an error.
    return df.rename(columns={"filename": "file_id", "damage": "prediction"})[["file_id", "prediction"]]


def iter_stress_files(uploaded_files):
    """Yield (file_id, file-like) pairs, expanding any uploaded zip archive into its members.

    A browser file input can't open a native folder picker, so "a folder of data"
    is supported by letting someone zip that folder and upload the archive directly,
    on top of plain multi-file selection. Whether something is an archive is decided
    by its actual content (zipfile.is_zipfile), not by its filename -- an upload
    named "data.txt" that's really a zip still gets unpacked, and a plain CSV named
    "export.zip" still gets read as a CSV.
    """
    for uploaded in uploaded_files:
        uploaded.seek(0)
        if zipfile.is_zipfile(uploaded):
            uploaded.seek(0)
            with zipfile.ZipFile(uploaded) as archive:
                for member in archive.namelist():
                    name = Path(member)
                    if member.endswith("/") or name.name.startswith((".", "__")):
                        continue
                    yield name.name, archive.open(member)
        else:
            uploaded.seek(0)
            yield uploaded.name, uploaded


def score_uploads(files) -> pd.DataFrame:
    rows = []
    skipped = []
    for name, f in iter_stress_files(files):
        try:
            rows.append({"file_id": name, "prediction": predict_damage(f)})
        except Exception:
            skipped.append(name)
    if skipped:
        st.warning(f"Skipped {len(skipped)} file(s) that weren't readable as a stress time series: {', '.join(skipped)}")
    return pd.DataFrame(rows)


def render_dashboard(df: pd.DataFrame) -> None:
    df = df.sort_values("prediction", ascending=False).reset_index(drop=True)
    top = df.iloc[0]

    cols = st.columns(3)
    cols[0].metric("Files scored", len(df))
    cols[1].metric("Highest damage", f"{top['prediction']:.3f}", help=top["file_id"])
    cols[2].metric("Mean damage", f"{df['prediction'].mean():.3f}")

    st.markdown("#### Damage by file")
    fig, ax = plt.subplots(figsize=(10, max(3, 0.35 * len(df))))
    ax.barh(df["file_id"], df["prediction"], color=ACCENT)
    ax.invert_yaxis()
    ax.set_xlabel("Predicted cumulative damage")
    fig.tight_layout()
    st.pyplot(fig)

    st.markdown("#### All files")
    st.dataframe(df.rename(columns={"prediction": "damage"}), width="stretch")

    st.download_button(
        "Download this result as CSV",
        df.to_csv(index=False),
        file_name="shm_predictions.csv",
        mime="text/csv",
    )


def record_upload(df: pd.DataFrame, uploaded_files) -> None:
    """Append one aggregate record for this upload (not one row per file)."""
    st.session_state.setdefault("shm_history", [])
    st.session_state.setdefault("shm_upload_count", 0)

    batch_key = tuple(sorted((f.name, f.size) for f in uploaded_files))
    if st.session_state.get("shm_last_batch_key") == batch_key:
        return  # a rerun with the same upload still selected, not a new one

    st.session_state.shm_last_batch_key = batch_key
    st.session_state.shm_upload_count += 1
    st.session_state.shm_history.append({
        "upload": f"Upload {st.session_state.shm_upload_count}",
        "files": len(df),
        "mean_damage": float(df["prediction"].mean()),
        "max_damage": float(df["prediction"].max()),
    })


def render_history() -> None:
    history = st.session_state.get("shm_history", [])
    if not history:
        return
    recent = pd.DataFrame(history[-HISTORY_LENGTH:])

    st.markdown(f"#### History (last {len(recent)} of {len(history)} uploads this session)")
    st.write("Mean and highest predicted damage per upload, so a trend across successive checks is visible at a glance.")

    x = range(len(recent))
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(x, recent["mean_damage"], marker="o", linestyle="-", color=ACCENT, label="Mean damage")
    ax.plot(x, recent["max_damage"], marker="o", linestyle="--", color=ACCENT, label="Max damage")
    ax.set_xticks(list(x))
    ax.set_xticklabels(recent["upload"], rotation=0, ha="center")
    ax.set_ylabel("Predicted damage")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)

    st.dataframe(
        recent.rename(columns={"upload": "Upload", "files": "Files", "mean_damage": "Mean damage", "max_damage": "Max damage"}),
        width="stretch",
        hide_index=True,
    )

    if st.button("Clear history"):
        st.session_state.shm_history = []
        st.rerun()


st.title("SHM subsystem — cumulative fatigue damage")
st.write(
    "Upload raw stress time-series data -- a single CSV, several at once, or a whole folder "
    "zipped up -- to estimate cumulative fatigue damage per file, or browse pre-computed "
    "sample results."
)

source = st.radio("Data source", ["Live prediction (upload raw stress data)", "Sample predictions"], horizontal=True)

if source == "Sample predictions":
    render_dashboard(load_sample())
else:
    uploaded = st.file_uploader(
        "Raw stress time-series data: pick one or more CSV files, or a single .zip of a whole "
        "folder of them. Any filename is accepted; content is what's checked.",
        accept_multiple_files=True,
    )
    if not uploaded:
        st.info("Upload raw stress files (or a zip of a folder of them) to estimate their fatigue damage.")
    else:
        with st.spinner("Rainflow-counting stress cycles..."):
            df = score_uploads(uploaded)
        render_dashboard(df)
        record_upload(df, uploaded)
        render_history()

        with st.expander("How this works"):
            st.markdown(
                "- Each file's raw stress signal is rainflow-counted into (stress range, cycle "
                "count) pairs -- the standard way to turn an irregular stress history into "
                "discrete load cycles for fatigue analysis.\n"
                "- A fatigue proxy is computed as `sum(count * stress_range ** 5.03)`, then scaled "
                "by a constant learned once from labeled training files "
                "(`damage = C × fatigue`, `C = 3.84e-11`) to produce the predicted cumulative "
                "damage.\n"
                "- That constant is fixed here rather than re-derived at runtime, since the raw "
                "SHM training data isn't bundled in this app -- see `final_predict.py` for the "
                "original derivation.\n"
                "- There's no severity threshold in the model itself -- it only outputs a "
                "continuous damage number -- so none is imposed here either."
            )

if st.button("← Back to overview", type="secondary"):
    st.switch_page("app.py")
