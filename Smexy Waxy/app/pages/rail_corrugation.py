import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

import rail_predict as rc
from components.styles import inject_download_button_style
from components.theme import THEME

st.set_page_config(page_title="Rail Corrugation | NebulaX PS3", page_icon="🛤️", layout="wide")
inject_download_button_style()

CLASS_COLORS = {"Normal": THEME["success"], "Side I": THEME["warning"], "Side II": THEME["rail_red"]}
RESULTS_KEY = "rail_results"


@st.cache_resource
def get_model_bundle() -> dict:
    return rc.load_model()


def count_items(uploaded_files) -> int:
    """How many files will be scored (zip archives count as their members)."""
    total = 0
    for uploaded in uploaded_files:
        uploaded.seek(0)
        try:
            if zipfile.is_zipfile(uploaded):
                uploaded.seek(0)
                with zipfile.ZipFile(uploaded) as archive:
                    total += sum(
                        1 for m in archive.namelist()
                        if not m.endswith("/") and not Path(m).name.startswith((".", "__"))
                    )
            else:
                total += 1
        except Exception:
            total += 1
    return total


def iter_uploaded_files(uploaded_files):
    """Yield (file_id, file-like) pairs, expanding any uploaded zip archive into its members.

    Files are streamed straight from the upload (no temp-file or in-memory copies). A problem
    with one uploaded item (a corrupted zip, an unreadable member) is reported by the caller
    as a skipped file rather than aborting the whole batch.
    """
    for uploaded in uploaded_files:
        try:
            uploaded.seek(0)
            if zipfile.is_zipfile(uploaded):
                uploaded.seek(0)
                with zipfile.ZipFile(uploaded) as archive:
                    for member in archive.namelist():
                        name = Path(member)
                        if member.endswith("/") or name.name.startswith((".", "__")):
                            continue
                        with archive.open(member) as handle:
                            yield name.name, handle
            else:
                uploaded.seek(0)
                yield uploaded.name, uploaded
        except Exception as exc:
            yield uploaded.name, exc


def predict_file(source) -> tuple[str, float]:
    bundle = get_model_bundle()
    model = bundle["model"]
    classes = list(model.classes_)
    boost = bundle.get("fault_boost", 1.0)
    normal = bundle.get("normal_label", "Normal")
    weights = np.array([1.0 if c == normal else boost for c in classes])

    df = pd.read_csv(source)
    row = rc.group_features(*rc.to_arrays(df))
    X = pd.DataFrame([row]).reindex(columns=bundle["base_features"])
    proba = model.predict_proba(X)[0]
    best = int(np.argmax(proba * weights))
    return classes[best], float(proba[best])


def score_all(uploaded_files) -> dict:
    """Score every file, updating a progress bar as it goes.

    Each update is a Streamlit call, which is also what lets Streamlit interrupt this
    run promptly if the user changes something -- a long loop with no such calls can't
    be stopped until it finishes.
    """
    total = count_items(uploaded_files)
    progress = st.progress(0.0, text=f"Scoring 0 / {total} files...")
    results: dict[str, tuple[str, float]] = {}
    skipped: dict[str, str] = {}

    for done, (file_id, source) in enumerate(iter_uploaded_files(uploaded_files), start=1):
        if isinstance(source, Exception):
            skipped[file_id] = f"couldn't read it as a file or archive ({source})"
        else:
            try:
                results[file_id] = predict_file(source)
            except Exception as exc:
                skipped[file_id] = f"couldn't read it as vibration/shock data ({exc})"
        progress.progress(min(done / max(total, 1), 1.0), text=f"Scored {done} / {total} files...")

    progress.empty()
    return {"results": results, "skipped": skipped}


st.title("Rail Corrugation subsystem — track condition classifier")
st.write(
    "Upload raw axle-box vibration/shock data -- one file, several at once, or a zipped folder "
    "of them -- then press **Run predictions** to classify each file as Normal, Side I, or "
    "Side II corrugation."
)

with st.form("rail_upload_form"):
    uploaded_files = st.file_uploader(
        "Vibration/shock data file(s) (any filename accepted -- content is what's checked)",
        accept_multiple_files=True,
    )
    submitted = st.form_submit_button("Run predictions", type="primary")

if submitted:
    if not uploaded_files:
        st.warning("Choose at least one file first.")
    else:
        st.session_state[RESULTS_KEY] = score_all(uploaded_files)

state = st.session_state.get(RESULTS_KEY)

if state is None:
    st.info("Choose files above, wait for them to finish uploading, then press Run predictions.")
else:
    results, skipped = state["results"], state["skipped"]

    if skipped:
        st.warning(f"Skipped {len(skipped)} file(s) that couldn't be read.")
        with st.expander("Which files, and why"):
            for file_id, reason in skipped.items():
                st.write(f"**{file_id}**: {reason}")

    if not results:
        st.error("None of the uploaded files could be scored.")
    else:
        st.markdown("#### Corrugation distribution")
        counts = pd.Series([prediction for prediction, _ in results.values()]).value_counts()
        fig, ax = plt.subplots(figsize=(2.2, 2.2))
        ax.pie(
            counts.values,
            labels=counts.index,
            colors=[CLASS_COLORS.get(label, THEME["text_secondary"]) for label in counts.index],
            autopct="%1.0f%%",
            startangle=90,
            textprops={"fontsize": 7},
        )
        ax.set_title(f"{len(results)} file(s) classified", fontsize=8)
        pie_col, _ = st.columns([1, 3])
        pie_col.pyplot(fig)
        plt.close(fig)

        st.markdown("#### Predictions Preview")
        overview = pd.DataFrame(
            {"file_id": file_id, "prediction": prediction, "confidence": confidence}
            for file_id, (prediction, confidence) in results.items()
        )
        st.dataframe(
            overview.rename(columns={"file_id": "File", "prediction": "Prediction", "confidence": "Confidence"}).style.format({"Confidence": "{:.0%}"}),
            width="stretch",
            hide_index=True,
        )

        predictions = pd.DataFrame(
            {"file_id": file_id, "prediction": prediction}
            for file_id, (prediction, _) in results.items()
        )
        st.download_button(
            "Download predictions.csv",
            predictions.to_csv(index=False),
            file_name="rail_predictions.csv",
            mime="text/csv",
        )

        with st.expander("How this works"):
            st.markdown(
                "- Each uploaded file's per-bearing vibration and shock signals (all cars, both "
                "track sides) are converted into ~280 summary statistics -- RMS, spread, spectral "
                "energy, and side/half comparisons across the train.\n"
                "- Those features are scored by a trained classifier (embedded in "
                "`rail_predict.py`, loaded once and cached) distinguishing Normal track from "
                "Side I / Side II corrugation.\n"
                "- A fault-boost weighting favors flagging Side I/II over Normal when the model "
                "is unsure, since missing real corrugation is costlier than a false alarm.\n"
                "- This model's training and validation live outside this repo; `rail_predict.py` "
                "ships with its fitted parameters embedded, so no separate training step runs "
                "here."
            )

if st.button("← Back to overview", type="secondary"):
    st.switch_page("app.py")
