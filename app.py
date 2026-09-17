import streamlit as st

from components.navigation import render_subsystem_card
from components.theme import SUBSYSTEMS, THEME


st.set_page_config(
    page_title="NebulaX PS3",
    page_icon="🚆",
    layout="wide",
)

st.markdown(
    f"""
    <style>
        :root {{
            --bg: {THEME['background']};
            --surface: {THEME['surface']};
            --surface-muted: {THEME['surface_muted']};
            --text: {THEME['text_primary']};
            --muted: {THEME['text_secondary']};
            --border: {THEME['border']};
            --red: {THEME['rail_red']};
            --green: {THEME['rail_green']};
            --orange: {THEME['rail_orange']};
            --blue: {THEME['rail_blue']};
            --success: {THEME['success']};
            --warning: {THEME['warning']};
        }}

        html, body, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"] {{
            font-family: "Times New Roman", Times, Georgia, serif;
            background: var(--bg);
            color: var(--text);
        }}

        .stApp {{
            background: var(--bg);
            color: var(--text);
        }}

        .block-container {{
            max-width: 1180px;
            padding-top: 2.5rem;
            padding-bottom: 3rem;
            margin: 0 auto;
        }}

        .topbar {{
            background: rgba(16, 41, 68, 0.65);
            border-bottom: 1px solid var(--border);
        }}

        h1, h2, h3, h4, .app-wordmark {{
            font-family: "Times New Roman", Times, Georgia, serif;
            font-weight: 700;
            letter-spacing: -0.01em;
            color: var(--text);
        }}

        .page-shell {{
            padding: 0.5rem 0 0.25rem;
        }}

        .app-header {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.65rem 0 1.2rem;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1.4rem;
        }}

        .wordmark {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            font-weight: 700;
            font-size: 1.05rem;
            color: var(--text);
            width: 100%;
            font-family: "Times New Roman", Times, Georgia, serif;
            text-align: center;
        }}

        .wordmark-ticks {{
            display: inline-flex;
            gap: 0.2rem;
        }}

        .wordmark-ticks span {{
            width: 0.3rem;
            height: 1.1rem;
            display: inline-block;
        }}

        .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.35rem 0.75rem;
            border: 1px solid var(--border);
            color: var(--muted);
            font-size: 0.85rem;
        }}

        .status-pill .dot {{
            width: 0.5rem;
            height: 0.5rem;
            border-radius: 50%;
            background: var(--blue);
            display: inline-block;
        }}

        .hero-block {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 1rem;
            align-items: center;
            justify-items: center;
            text-align: center;
            margin-bottom: 1.5rem;
        }}

        .lead-heading {{
            font-family: "Times New Roman", Times, Georgia, serif !important;
            font-size: clamp(2.3rem, 3.4vw, 3.6rem);
            line-height: 1.08;
            margin: 0 0 0.7rem 0;
            letter-spacing: -0.01em;
            text-align: center;
        }}

        .lead-copy {{
            font-family: "Times New Roman", Times, Georgia, serif;
            color: var(--muted);
            font-size: 1.08rem;
            line-height: 1.85;
            max-width: 50rem;
            width: 100%;
            margin: 0 auto;
            text-align: center;
        }}

        .section-title {{
            font-family: "Times New Roman", Times, Georgia, serif;
            margin-top: 1.4rem;
            margin-bottom: 0.9rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--text);
            text-align: center;
            font-family: "Times New Roman", Times, Georgia, serif;
        }}

        .subsystem-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1rem;
        }}

        [data-testid="column"] {{
            text-align: center;
        }}

        .stButton > button {{
            border-radius: 2px;
            border: 1px solid var(--border);
            background: transparent;
            color: var(--text);
            font-family: "Times New Roman", Times, Georgia, serif;
            font-weight: 700;
            padding: 0.7rem 1rem;
            margin-top: 0.95rem;
            transition: background 0.15s ease, color 0.15s ease;
        }}

        .stButton > button:hover {{
            background: var(--blue);
            border-color: var(--blue);
            color: #FFFFFF;
        }}

        .stButton > button:focus {{
            box-shadow: 0 0 0 0.15rem rgba(74, 143, 224, 0.3);
            outline: none;
        }}

        .note-bar {{
            margin-top: 1.6rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            color: var(--muted);
            font-size: 0.9rem;
            text-align: center;
        }}

        @media (max-width: 760px) {{
            .hero-block, .subsystem-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="page-shell">
        <div class="app-header">
            <div class="wordmark">
                <span class="wordmark-ticks">
                    <span style="background: var(--red);"></span>
                    <span style="background: var(--green);"></span>
                    <span style="background: var(--orange);"></span>
                    <span style="background: var(--blue);"></span>
                </span>
                <span>NebulaX : PS3</span>
                <span class="wordmark-ticks">
                    <span style="background: var(--blue);"></span>
                    <span style="background: var(--orange);"></span>
                    <span style="background: var(--green);"></span>
                    <span style="background: var(--red);"></span>
                </span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-block">
        <h1 class="lead-heading">Train condition monitoring</h1>
        <p class="lead-copy">Each panel below tracks telemetry for one subsystem. Open one to review recent
        readings and current fault indicators.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='section-title'>Subsystem overview</div>", unsafe_allow_html=True)

columns = st.columns(2)
for idx, subsystem in enumerate(SUBSYSTEMS):
    with columns[idx % 2]:
        render_subsystem_card(subsystem)