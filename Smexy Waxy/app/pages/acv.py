import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

from acv_features import explain_top_pick, get_or_train_model, load_case, score_file
from components.styles import inject_download_button_style

st.set_page_config(page_title="ACV | NebulaX PS3", page_icon="❄️", layout="wide")
inject_download_button_style()


@st.cache_resource
def get_model():
    return get_or_train_model()


def _is_workbook_zip(archive: zipfile.ZipFile) -> bool:
    """True if this zip's content IS an .xlsx workbook, not a folder of separate files.

    .xlsx is itself a zip container, so a plain zipfile.is_zipfile() check can't tell
    "someone uploaded one workbook" from "someone uploaded a zipped folder of workbooks"
    -- an Office document always has this internal structure, a folder of files won't.
    """
    names = archive.namelist()
    return "[Content_Types].xml" in names or any(n.startswith("xl/") for n in names)


def iter_uploaded_files(uploaded_files):
    """Yield (file_id, local_path) pairs, expanding any uploaded *folder* zip into its members.

    A browser file input can't open a native folder picker, so "a folder of data" is
    supported by letting someone zip that folder and upload the archive directly, on
    top of plain multi-file selection.
    """
    tmp_dir = Path(tempfile.mkdtemp())
    for uploaded in uploaded_files:
        uploaded.seek(0)
        is_folder_zip = False
        if zipfile.is_zipfile(uploaded):
            uploaded.seek(0)
            with zipfile.ZipFile(uploaded) as archive:
                is_folder_zip = not _is_workbook_zip(archive)
                if is_folder_zip:
                    for member in archive.namelist():
                        name = Path(member)
                        if member.endswith("/") or name.name.startswith((".", "__")):
                            continue
                        dest = tmp_dir / name.name
                        dest.write_bytes(archive.read(member))
                        yield name.name, dest
        if not is_folder_zip:
            uploaded.seek(0)
            dest = tmp_dir / uploaded.name
            dest.write_bytes(uploaded.getvalue())
            yield uploaded.name, dest


st.title("ACV subsystem — refrigerant-leak locator")
st.write(
    "Upload ACV telemetry workbooks -- one, several at once, or a zipped folder of them -- "
    "to rank each file's cars from most- to least-likely to have the refrigerant leak."
)

uploaded_files = st.file_uploader(
    "ACV telemetry workbook(s) (any filename accepted -- content is what's checked)",
    accept_multiple_files=True,
)

if not uploaded_files:
    st.info("Upload one or more workbooks to see predictions.")
else:
    model = get_model()
    results: dict[str, pd.DataFrame] = {}
    with st.spinner("Scoring every car against its peers..."):
        for file_id, path in iter_uploaded_files(uploaded_files):
            try:
                results[file_id] = score_file(load_case(path), model)
            except Exception as exc:
                st.warning(f"Skipped {file_id}: couldn't read it as ACV telemetry ({exc}).")

    if not results:
        st.error("None of the uploaded files could be read as ACV telemetry.")
    else:
        for file_id, ranked in results.items():
            top_car = ranked.index[0]
            top = ranked.iloc[0]
            with st.container(border=True):
                st.subheader(f"{file_id}: most likely fault Car {top_car}")
                st.progress(min(max(top["probability"], 0.0), 1.0), text=f"Estimated probability: {top['probability']:.0%}")
                st.write(explain_top_pick(ranked))

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

        predictions = pd.DataFrame(
            {"file_id": file_id, "ranked_cars": "|".join(ranked.index)}
            for file_id, ranked in results.items()
        )
        st.download_button(
            "Download predictions.csv",
            predictions.to_csv(index=False),
            file_name="acv_predictions.csv",
            mime="text/csv",
        )

        with st.expander("How this works"):
            st.markdown(
                "- One number per car: how far its cabin temperature sits above its own cooling "
                "setpoint while actively cooling, compared to its 7 peers in the same file. Rows "
                "the file itself flags `Invalid` are excluded first.\n"
                "- That gap is the textbook signature of reduced cooling capacity from a "
                "refrigerant leak; it's converted into a probability by a single-feature logistic "
                "regression trained on the documented leak cases (loaded from a saved model "
                "artifact, `acv_model.joblib`, when present).\n"
                "- One of the six labeled training files uses an entirely different, much richer "
                "column layout the feature can't be computed from, so it's excluded from training "
                "rather than special-cased.\n"
                "- Validated with leave-one-file-out cross-validation across the five usable "
                "labeled files: every one ranks the true faulty car 1st.\n"
                "- Full methodology and validation: [acv_eda.ipynb](../acv_eda.ipynb)."
            )

if st.button("← Back to overview", type="secondary"):
    st.switch_page("app.py")
