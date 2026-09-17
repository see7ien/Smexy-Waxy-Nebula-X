import streamlit as st

from components.theme import ACCENT_MAP


def render_subsystem_card(subsystem):
    accent = ACCENT_MAP[subsystem["key"]]

    with st.container():
        st.markdown(
            f"<div style='height:4px; border-radius:999px; background:{accent['color']}; margin-bottom:0.8rem;'></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='margin-top:0.7rem; text-align:center; font-size:1.55rem; font-weight:700; letter-spacing:-0.04em; color:{accent['color']}; font-family:Times New Roman, serif;'>{subsystem['title']}</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div style='margin-top:0.9rem; color:#FFFFFF; line-height:1.6; min-height:3.25rem; text-align:center; font-family:Times New Roman, serif;'>{subsystem['description']}</div>",
            unsafe_allow_html=True,
        )

        if st.button(
            f"Open {subsystem['title']} workflow",
            use_container_width=True,
            key=f"nav_{subsystem['key']}",
        ):
            st.switch_page(subsystem["path"])
