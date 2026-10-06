"""Centralized dark-institutional design system for the dashboard.

One source of truth for colors, semantic meaning, and global CSS. Every page
calls :func:`configure_page` exactly once, and all charts read their colors from
:data:`SEMANTIC` / :data:`PALETTE` so calm/stress/resilience are consistent
everywhere.
"""

from __future__ import annotations

import streamlit as st


# --- Core surface palette -----------------------------------------------------

PALETTE = {
    "bg": "#0B1220",          # app background (deep navy/graphite)
    "panel": "#111A2E",       # card / panel background
    "elevated": "#172033",    # elevated surface / hover
    "border": "#243044",      # hairline borders
    "grid": "#1C2942",        # chart gridlines
    "text": "#F3F4F6",        # primary text
    "text_muted": "#94A3B8",  # secondary text
    "text_faint": "#64748B",  # captions / de-emphasized
}

# --- Semantic colors (meaning is fixed across the whole app) ------------------

SEMANTIC = {
    "calm": "#57A6E5",              # calm regime -> blue
    "stress": "#F0883E",           # stress regime -> warm orange
    "resilient": "#33B79B",        # diversifies better in stress -> teal/green
    "vol_sensitive": "#E8A33D",    # volatility-driven increase -> amber
    "robust": "#E5484D",           # robust breakdown -> red
    "mostly_resilient": "#6E86B8", # small adjusted increase -> muted slate-blue
    "inconclusive": "#64748B",     # neutral slate/grey
    "neutral": "#8B98AD",
}

# Forbes-Rigobon fragility class -> color (imported by FR + Pair pages).
from app.utils.constants import (  # noqa: E402
    FR_MOSTLY_RESILIENT,
    FR_RESILIENT,
    FR_ROBUST,
    FR_UNAVAILABLE,
    FR_VOL_SENSITIVE,
)

FR_CLASS_COLORS = {
    FR_ROBUST: SEMANTIC["robust"],
    FR_VOL_SENSITIVE: SEMANTIC["vol_sensitive"],
    FR_MOSTLY_RESILIENT: SEMANTIC["mostly_resilient"],
    FR_RESILIENT: SEMANTIC["resilient"],
    FR_UNAVAILABLE: SEMANTIC["inconclusive"],
}

# Diverging correlation scale: negative (decouple) -> blue, ~0 -> dark, positive
# (tighten) -> orange. Positive change maps to the stress color by design.
CORR_DIVERGING = [
    [0.0, SEMANTIC["calm"]],
    [0.5, PALETTE["panel"]],
    [1.0, SEMANTIC["stress"]],
]


def _global_css() -> str:
    p = PALETTE
    return f"""
    <style>
    :root {{
        --ds-bg: {p['bg']};
        --ds-panel: {p['panel']};
        --ds-elevated: {p['elevated']};
        --ds-border: {p['border']};
        --ds-text: {p['text']};
        --ds-muted: {p['text_muted']};
        --ds-faint: {p['text_faint']};
    }}
    .stApp {{ background: {p['bg']}; }}
    .block-container {{ padding-top: 1.4rem; padding-bottom: 2.2rem; max-width: 1500px; }}
    section[data-testid="stSidebar"] {{
        background: {p['panel']};
        border-right: 1px solid {p['border']};
    }}
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stMultiSelect label {{
        color: {p['muted'] if 'muted' in p else p['text_muted']};
        font-size: 0.82rem; font-weight: 600; letter-spacing: 0.02em;
    }}
    /* Eyebrow + page header */
    .ds-eyebrow {{
        color: {SEMANTIC['stress']};
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.18em;
        text-transform: uppercase; margin-bottom: 0.15rem;
    }}
    .ds-h1 {{
        color: {p['text']}; font-size: 1.72rem; font-weight: 720;
        line-height: 1.16; margin: 0 0 0.30rem 0;
    }}
    .ds-sub {{
        color: {p['text_muted']}; font-size: 0.98rem; font-weight: 400;
        line-height: 1.4; margin: 0 0 0.2rem 0; max-width: 900px;
    }}
    .ds-section {{
        color: {p['text']}; font-size: 0.80rem; font-weight: 700;
        letter-spacing: 0.13em; text-transform: uppercase;
        margin: 1.35rem 0 0.55rem 0; padding-bottom: 0.35rem;
        border-bottom: 1px solid {p['border']};
    }}
    .ds-caption {{ color: {p['text_faint']}; font-size: 0.82rem; line-height: 1.4; }}
    /* Stat cards */
    .ds-card {{
        background: {p['panel']}; border: 1px solid {p['border']};
        border-radius: 10px; padding: 0.72rem 0.9rem; height: 100%;
    }}
    .ds-card .lab {{
        color: {p['text_muted']}; font-size: 0.74rem; font-weight: 600;
        letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 0.28rem;
    }}
    .ds-card .val {{ color: {p['text']}; font-size: 1.42rem; font-weight: 720; line-height: 1.1; }}
    .ds-card .delta {{ font-size: 0.82rem; font-weight: 600; margin-top: 0.18rem; }}
    .ds-card .sub {{ color: {p['text_faint']}; font-size: 0.76rem; margin-top: 0.18rem; line-height: 1.3; }}
    /* Interpretation panel */
    .ds-interp {{
        background: {p['elevated']};
        border: 1px solid {p['border']};
        border-radius: 10px; padding: 0.95rem 1.1rem; margin-top: 0.4rem;
    }}
    .ds-interp .head {{
        color: {p['text_muted']}; font-size: 0.72rem; font-weight: 700;
        letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.4rem;
    }}
    .ds-interp p {{ color: {p['text']}; font-size: 0.94rem; line-height: 1.5; margin: 0 0 0.45rem 0; }}
    .ds-interp p:last-child {{ margin-bottom: 0; }}
    .ds-interp b {{ color: #FFFFFF; }}
    /* Chips */
    .ds-chip {{
        display: inline-block; padding: 0.12rem 0.55rem; border-radius: 999px;
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.02em;
    }}
    .ds-official {{ background: rgba(87,166,229,0.14); color: {SEMANTIC['calm']}; border: 1px solid rgba(87,166,229,0.35); }}
    .ds-exploratory {{ background: rgba(240,136,62,0.12); color: {SEMANTIC['stress']}; border: 1px solid rgba(240,136,62,0.32); }}
    /* Native metric restyle (used where st.metric remains) */
    div[data-testid="stMetric"] {{
        background: {p['panel']}; border: 1px solid {p['border']};
        border-radius: 10px; padding: 0.7rem 0.85rem;
    }}
    div[data-testid="stMetricLabel"] p {{ color: {p['text_muted']}; font-weight: 600; }}
    /* Tabs + dataframe polish */
    button[data-baseweb="tab"] {{ font-weight: 600; }}
    .stDataFrame {{ border: 1px solid {p['border']}; border-radius: 8px; }}
    /* Pipeline diagram */
    .ds-pipe {{ display: flex; align-items: stretch; gap: 0; flex-wrap: wrap; margin-top: 0.4rem; }}
    .ds-pipe-step {{
        flex: 1 1 0; min-width: 120px; background: {p['panel']};
        border: 1px solid {p['border']}; border-radius: 10px;
        padding: 0.6rem 0.7rem; margin: 0 0.22rem;
    }}
    .ds-pipe-step .n {{ color: {SEMANTIC['stress']}; font-size: 0.70rem; font-weight: 700; letter-spacing: 0.08em; }}
    .ds-pipe-step .t {{ color: {p['text']}; font-size: 0.86rem; font-weight: 650; margin-top: 0.15rem; line-height: 1.2; }}
    .ds-pipe-step .d {{ color: {p['text_faint']}; font-size: 0.72rem; margin-top: 0.2rem; line-height: 1.28; }}
    /* Finding cards (home) */
    .ds-find {{
        background: {p['panel']}; border: 1px solid {p['border']};
        border-radius: 12px; padding: 1.0rem 1.1rem; height: 100%;
    }}
    .ds-find .k {{ font-size: 1.5rem; font-weight: 760; line-height: 1.05; }}
    .ds-find .h {{ color: {p['text']}; font-size: 0.98rem; font-weight: 680; margin: 0.35rem 0 0.3rem 0; line-height: 1.25; }}
    .ds-find .b {{ color: {p['text_muted']}; font-size: 0.85rem; line-height: 1.45; }}
    .ds-hero-title {{ color: {p['text']}; font-size: 2.35rem; font-weight: 760; line-height: 1.08; margin: 0.1rem 0 0.2rem 0; }}
    .ds-hero-sub {{ color: {SEMANTIC['calm']}; font-size: 1.05rem; font-weight: 600; margin-bottom: 0.5rem; }}
    .ds-hero-q {{ color: {p['text_muted']}; font-size: 1.0rem; font-style: italic; max-width: 780px; }}
    </style>
    """


def configure_page(title: str, icon: str = "◆") -> None:
    """Set page config and inject the global design-system CSS (call once per page)."""
    st.set_page_config(page_title=f"{title} · Stress-Regime Explorer", page_icon=icon, layout="wide")
    st.markdown(_global_css(), unsafe_allow_html=True)


def delta_color(value: float, *, good_when_negative: bool = False) -> str:
    """Semantic color for a signed change (neutral by default, not judgmental)."""
    if value is None:
        return PALETTE["text_faint"]
    if abs(value) < 1e-9:
        return PALETTE["text_faint"]
    positive = value > 0
    if good_when_negative:
        positive = not positive
    return SEMANTIC["stress"] if value > 0 else SEMANTIC["calm"]
