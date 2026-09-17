import streamlit as st


st.set_page_config(page_title="SHM | NebulaX PS3", page_icon="📡", layout="wide")

st.title("Structural health monitoring")
st.write(
    "Inspect structural condition signals and vibration patterns to support monitoring of train health and dynamic stability."
)
st.write("The SHM workflow will accept monitored data once the model is attached.")

with st.container(border=True):
    st.subheader("Current workflow")
    st.write("This page is a structured placeholder for the SHM analysis pipeline.")
    st.markdown(
        "- Expected input: vibration, acceleration, and structural health measurements\n"
        "- Expected output: condition summaries and evidence-led maintenance guidance"
    )

if st.button("← Back to overview", type="secondary"):
    st.switch_page("app.py")
