import streamlit as st


st.set_page_config(page_title="Rail Corrugation | NebulaX PS3", page_icon="🛤️", layout="wide")

st.title("Rail corrugation")
st.write(
    "Assess track surface condition, vibration signatures, and signal quality used to detect rail corrugation and related wear patterns."
)
st.write("The analysis workflow is defined, but the inference stage is not connected yet.")

with st.container(border=True):
    st.subheader("Current workflow")
    st.write("This page is a placeholder for the rail-condition monitoring workflow.")
    st.markdown(
        "- Expected input: rail vibration and condition data streams\n"
        "- Expected output: defect summaries, severity review, and maintenance prioritisation notes"
    )

if st.button("← Back to overview", type="secondary"):
    st.switch_page("app.py")
