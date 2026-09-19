import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import rail_predict as rc

st.set_page_config(page_title="Rail Corrugation | NebulaX PS3", page_icon="🛤️", layout="wide")


@st.cache_resource
def get_model_bundle() -> dict:
    return rc.load_model()


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
    "Upload a raw axle-box vibration/shock CSV (bearing signals across all cars) and this page "
    "classifies the file as Normal, Side I, or Side II corrugation."
)

uploaded = st.file_uploader("Vibration/shock data file (any filename accepted -- content is what's checked)")

if uploaded is None:
    st.info("Upload a CSV to see a prediction.")
else:
    tmp_dir = Path(tempfile.mkdtemp())
    csv_path = tmp_dir / uploaded.name
    csv_path.write_bytes(uploaded.getvalue())

    with st.spinner("Extracting bearing features and scoring..."):
        prediction, proba = predict_file(csv_path)

    with st.container(border=True):
        st.subheader(f"Prediction: {prediction}")
        st.progress(min(max(float(proba[prediction]), 0.0), 1.0), text=f"Confidence: {proba[prediction]:.0%}")

    st.markdown("#### Class probabilities")
    st.bar_chart(proba, y_label="Probability")

    st.download_button(
        "Download this result as CSV",
        pd.DataFrame({"file_id": [uploaded.name], "prediction": [prediction]}).to_csv(index=False),
        file_name="rail_predictions.csv",
        mime="text/csv",
    )

    with st.expander("How this works"):
        st.markdown(
            "- The uploaded CSV's per-bearing vibration and shock signals (all cars, both track "
            "sides) are converted into ~280 summary statistics per file -- RMS, spread, spectral "
            "energy, and side/half comparisons across the train.\n"
            "- Those features are scored by a trained classifier (embedded in `rail_predict.py`, "
            "loaded once and cached) distinguishing Normal track from Side I / Side II "
            "corrugation.\n"
            "- A fault-boost weighting favors flagging Side I/II over Normal when the model is "
            "unsure, since missing real corrugation is costlier than a false alarm.\n"
            "- This model's training and validation live outside this repo; `rail_predict.py` "
            "ships with its fitted parameters embedded, so no separate training step runs here."
        )

if st.button("← Back to overview", type="secondary"):
    st.switch_page("app.py")
