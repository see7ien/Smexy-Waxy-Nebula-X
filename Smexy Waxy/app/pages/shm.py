import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from components.styles import inject_download_button_style
from components.theme import ACCENT_MAP
from shm_features import predict_damage

ACCENT = ACCENT_MAP["shm"]["color"]

st.set_page_config(page_title="SHM | NebulaX PS3", page_icon="📡", layout="wide")
inject_download_button_style()


def iter_stress_files(uploaded_files):
    """Yield (file_id, file-like) pairs, expanding any uploaded zip archive into its members.

    A browser file input can't open a native folder picker, so "a folder of data" is
    supported by letting someone zip that folder and upload the archive directly, on
    top of plain multi-file selection. Whether something is an archive is decided by
    its actual content (zipfile.is_zipfile), not by its filename.
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
    bars = ax.barh(df["file_id"], df["prediction"], color=ACCENT)
    ax.invert_yaxis()
    ax.set_xlabel("Predicted cumulative damage")
    ax.set_xlim(0, df["prediction"].max() * 1.2 or 1)
    ax.bar_label(bars, fmt="%.3f", padding=4)
    fig.tight_layout()
    st.pyplot(fig)

    st.markdown("#### Predictions Preview")
    st.dataframe(df.rename(columns={"prediction": "damage"}), width="stretch")

    st.download_button(
        "Download predictions.csv",
        df.to_csv(index=False),
        file_name="shm_predictions.csv",
        mime="text/csv",
    )


st.title("SHM subsystem — cumulative fatigue damage")
st.write(
    "Upload raw stress time-series data -- a single CSV, several at once, or a whole folder "
    "zipped up -- to estimate cumulative fatigue damage per file."
)

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

    if df.empty:
        st.error("None of the uploaded files could be scored.")
    else:
        render_dashboard(df)

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
                "SHM training data isn't bundled in this app.\n"
                "- There's no severity threshold in the model itself -- it only outputs a "
                "continuous damage number -- so none is imposed here either."
            )

if st.button("← Back to overview", type="secondary"):
    st.switch_page("app.py")
