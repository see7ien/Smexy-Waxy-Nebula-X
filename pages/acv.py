import streamlit as st


st.set_page_config(page_title="ACV | NebulaX PS3", page_icon="❄️", layout="wide")

st.title("ACV subsystem")
st.write(
    "Review climate-control and ventilation behaviour to check for unstable operating states and degraded airflow conditions."
)
st.write("This workflow is ready for the model pipeline to be attached once the live inference link is available.")

with st.container(border=True):
    st.subheader("Current workflow")
    st.write("This placeholder page defines the intended ACV condition-monitoring flow.")
    st.markdown(
        "- Expected input: HVAC telemetry, airflow metrics, and system state logs\n"
        "- Expected output: trend review, operational anomalies, and flagged health states"
    )

if st.button("← Back to overview", type="secondary"):
    st.switch_page("app.py")
