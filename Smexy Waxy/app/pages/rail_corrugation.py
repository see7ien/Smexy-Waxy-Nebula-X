import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import rail_predict as rc
from components.styles import inject_download_button_style

st.set_page_config(page_title="Rail Corrugation | NebulaX PS3", page_icon="🛤️", layout="wide")
inject_download_button_style()


@st.cache_resource
def get_model_bundle() -> dict:
    return rc.load_model()


def iter_uploaded_files(uploaded_files):
    """Yield (file_id, local_path) pairs, expanding any uploaded zip archive into its members."""
    tmp_dir = Path(tempfile.mkdtemp())
    for uploaded in uploaded_files:
        uploaded.seek(0)
        if zipfile.is_zipfile(uploaded):
            uploaded.seek(0)
            with zipfile.ZipFile(uploaded) as archive:
                for member in archive.namelist():
                    name = Path(member)
                    if member.endswith("/") or name.name.startswith((".", "__")):
                        continue
                    dest = tmp_dir / name.name
                    dest.write_bytes(archive.read(member))
                    yield name.name, dest
        else:
            uploaded.seek(0)
            dest = tmp_dir / uploaded.name
            dest.write_bytes(uploaded.getvalue())
            yield uploaded.name, dest


def predict_file(path: Path) -> tuple[str, pd.Series]:
    bundle = get_model_bundle()
    model = bundle["model"]
    classes = list(model.classes_)
    boost = bundle.get("fault_boost", 1.0)
    normal = bundle.get("normal_label", "Normal")
    weights = np.array([1.0 if c == normal else boost for c in classes])

    df = pd.read_csv(path)
    row = rc.group_features(*rc.to_arrays(df))
    X = pd.DataFrame([row]).reindex(columns=bundle["base_features"])
    proba = model.predict_proba(X)[0]
    prediction = classes[int(np.argmax(proba * weights))]
    return prediction, pd.Series(proba, index=classes)


st.title("Rail Corrugation subsystem — track condition classifier")
st.write(
    "Upload raw axle-box vibration/shock data -- one file, several at once, or a zipped folder "
    "of them -- to classify each file as Normal, Side I, or Side II corrugation."
)

uploaded_files = st.file_uploader(
    "Vibration/shock data file(s) (any filename accepted -- content is what's checked)",
    accept_multiple_files=True,
)

if not uploaded_files:
    st.info("Upload one or more files to see predictions.")
else:
    results: dict[str, tuple[str, pd.Series]] = {}
    with st.spinner("Extracting bearing features and scoring..."):
        for file_id, path in iter_uploaded_files(uploaded_files):
            try:
                results[file_id] = predict_file(path)
            except Exception as exc:
                st.warning(f"Skipped {file_id}: couldn't read it as vibration/shock data ({exc}).")

    if not results:
        st.error("None of the uploaded files could be scored.")
    else:
        st.markdown("#### Overview")
        overview = pd.DataFrame(
            {
                "file_id": file_id,
                "prediction": prediction,
                "confidence": proba[prediction],
            }
            for file_id, (prediction, proba) in results.items()
        )
        st.dataframe(
            overview.rename(columns={"file_id": "File", "prediction": "Prediction", "confidence": "Confidence"}).style.format({"Confidence": "{:.0%}"}),
            width="stretch",
            hide_index=True,
        )

        st.markdown("#### Per-file detail")
        st.write("Click a file below to see its full Normal / Side I / Side II breakdown.")
        for file_id, (prediction, proba) in results.items():
            with st.expander(f"{file_id}: {prediction} ({proba[prediction]:.0%} confidence)"):
                st.bar_chart(proba, y_label="Probability")

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
