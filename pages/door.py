import streamlit as st


st.set_page_config(page_title="Door | NebulaX PS3", page_icon="🚪", layout="wide")

st.title("Door subsystem")
st.write(
    "Inspect door cycle behaviour, event timing, and abnormal operation patterns to support condition-monitoring review."
)
st.write("This workflow is ready for event data and diagnostics once the model pipeline is connected.")

with st.container(border=True):
    st.subheader("Current workflow")
    st.write("This page is a placeholder for the door monitoring workflow.")
    st.markdown(
        "- Expected input: door event logs, cycle timing signals, and operating state records\n"
        "- Expected output: fault summaries, anomaly review, and maintenance-ready diagnostics"
    )

if st.button("← Back to overview", type="secondary"):
    st.switch_page("app.py")
