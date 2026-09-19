import streamlit as st

from components.theme import THEME


def inject_download_button_style() -> None:
    """Make every st.download_button on the page large, centered, and already
    highlighted solid red (the home page's wordmark accent) -- not just on hover."""
    st.markdown(
        f"""
        <style>
            div[data-testid="stDownloadButton"] {{
                width: 100%;
                text-align: center;
                margin: 2rem 0;
            }}
            div[data-testid="stDownloadButton"] button {{
                display: block;
                margin: 0 auto;
                border: 3px solid {THEME['rail_red']};
                color: #FFFFFF;
                background: {THEME['rail_red']};
                font-weight: 700;
                font-size: 1.9rem;
                padding: 1.6rem 4rem;
                border-radius: 6px;
                width: 90%;
                max-width: 36rem;
            }}
            div[data-testid="stDownloadButton"] button:hover {{
                background: #FFFFFF;
                color: {THEME['rail_red']};
            }}
            div[data-testid="stDownloadButton"] button p {{
                font-size: 1.9rem !important;
                font-weight: 700 !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
