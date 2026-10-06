"""Stress-Regime Research Explorer — landing page.

Refactored dark-institutional home: research hero, three sourced empirical
findings, the analysis pipeline, module navigation, and a compact regime
preview. Data-readiness diagnostics live in a technical expander.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from app.utils.components import (  # noqa: E402
    caption, finding_card, module_card, pipeline_diagram, section,
)
from app.utils.data import list_parquet_exports, load_parquet  # noqa: E402
from app.utils.db import database_exists, duckdb_table_overview  # noqa: E402
from app.utils.formatting import human_bytes, human_datetime, human_int, status_label  # noqa: E402
from app.utils.paths import APP_DATA_DIR, DB_PATH, repo_relative  # noqa: E402
from app.utils.plotting import finalize  # noqa: E402
from app.utils.theme import PALETTE, SEMANTIC, configure_page  # noqa: E402

configure_page("Home")


# --- Hero ---------------------------------------------------------------------

st.markdown('<div class="ds-eyebrow">Data Science in Finance · TUM</div>', unsafe_allow_html=True)
hero_left, hero_right = st.columns([1.35, 1])
with hero_left:
    st.markdown(
        f"""
        <div class="ds-hero-title">Safe Until It Isn&#39;t</div>
        <div class="ds-hero-sub">Interactive Stress-Regime Diversification Research Explorer</div>
        <div class="ds-hero-q">How does diversification change when markets move from calm into stress —
        and is the deterioration a structural break in dependence, or a mechanical consequence of higher volatility?</div>
        """,
        unsafe_allow_html=True,
    )


def _stress_segments(dates: pd.Series, flags: pd.Series):
    dates = pd.to_datetime(dates).reset_index(drop=True)
    flags = flags.fillna(False).astype(bool).reset_index(drop=True)
    segments, start, prev = [], None, None
    for d, f in zip(dates, flags):
        if f and start is None:
            start = d
        elif not f and start is not None:
            segments.append((start, prev))
            start = None
        prev = d
    if start is not None:
        segments.append((start, prev))
    return segments


@st.cache_data(show_spinner=False)
def _regime_preview() -> pd.DataFrame:
    frame = load_parquet("regime_timeseries.parquet")
    if frame.empty:
        return frame
    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["spy_adj_close"] = pd.to_numeric(frame["spy_adj_close"], errors="coerce")
    if "ms_stress_50_monthly" in frame.columns:
        frame["stress"] = frame["ms_stress_50_monthly"].fillna(0).astype(float) > 0
    else:
        frame["stress"] = frame.get("ms_prob_stress_monthly", 0).fillna(0).astype(float) >= 0.5
    return frame.sort_values("date").reset_index(drop=True)


preview = _regime_preview()
with hero_right:
    if preview.empty:
        st.info("Regime preview unavailable — export dashboard data.")
    else:
        fig = go.Figure()
        for x0, x1 in _stress_segments(preview["date"], preview["stress"]):
            fig.add_vrect(x0=x0, x1=x1 + pd.Timedelta(days=1), fillcolor=SEMANTIC["stress"],
                          opacity=0.16, line_width=0, layer="below")
        fig.add_trace(go.Scatter(
            x=preview["date"], y=preview["spy_adj_close"], mode="lines",
            line=dict(color=SEMANTIC["calm"], width=1.4), name="SPY",
            hovertemplate="%{x|%Y-%m-%d}<br>SPY: %{y:.0f}<extra></extra>",
        ))
        fig.update_yaxes(type="log", title_text="SPY (log)")
        finalize(fig, 210, margin=dict(l=44, r=10, t=16, b=24))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        caption("SPY with official monthly Markov stress months shaded — the regime every module conditions on.")


# --- Three central empirical findings ----------------------------------------

section("Three empirical findings")
f1, f2, f3 = st.columns(3)
with f1:
    st.markdown(
        finding_card(
            SEMANTIC["stress"], "PC1  0.79 → 0.89",
            "International equity compresses sharply in stress",
            "Across six equity markets the average pairwise correlation rises from 0.74 to 0.87 and the "
            "leading component absorbs ~89% of variance — barely more than one effective bet (1.58 → 1.26).",
        ),
        unsafe_allow_html=True,
    )
with f2:
    st.markdown(
        finding_card(
            SEMANTIC["calm"], "ρ̄  −0.02   ·   PC1  +0.07",
            "A flat average correlation can hide concentration",
            "The cross-asset universe shows a nearly flat average correlation in stress (0.195 → 0.170), yet "
            "PC1 share still rises (0.31 → 0.37) and effective bets fall (4.52 → 4.33): a system-level reshuffle.",
        ),
        unsafe_allow_html=True,
    )
with f3:
    st.markdown(
        finding_card(
            SEMANTIC["resilient"], "SPY–TLT  −0.36 → +0.10",
            "Cross-asset hedges are episode-dependent",
            "The Treasury hedge is resilient on average but flips sign in the 2022–2023 inflation stress, while "
            "gold (SPY–GLD) stays within [+0.01, +0.15] across every episode — comparatively stable.",
        ),
        unsafe_allow_html=True,
    )
caption("Figures are read from the project's stored pipeline outputs (PCA, correlation, and stress-episode tables).")


# --- Pipeline -----------------------------------------------------------------

section("Research pipeline")
pipeline_diagram()


# --- Module navigation --------------------------------------------------------

section("Analytical modules")
modules = [
    ("pages/1_Regime_Explorer.py", "Regime Explorer",
     "When was the market stressed, and how sensitive is that classification?"),
    ("pages/2_Correlation_Matrices.py", "Correlation Matrices",
     "Which relationships tighten or decouple when stress arrives?"),
    ("pages/3_Pair_Stress_Lab.py", "Pair Stress Lab",
     "For one pair: raw change, bootstrap significance, and the volatility adjustment."),
    ("pages/4_PCA_Concentration.py", "PCA Concentration",
     "Does the universe collapse onto fewer independent risk directions?"),
    ("pages/5_Stress_Anatomy.py", "Stress Anatomy",
     "Does diversification behave the same way in every type of stress?"),
    ("pages/6_Forbes_Rigobon.py", "Forbes–Rigobon",
     "Do raw correlation increases survive adjustment for higher volatility?"),
    ("pages/7_Portfolio_X_Ray.py", "Portfolio X-Ray",
     "Build a portfolio and inspect how its diversification changes under stress."),
]
rows = [modules[i:i + 3] for i in range(0, len(modules), 3)]
for row in rows:
    cols = st.columns(3)
    for col, (target, title, desc) in zip(cols, row):
        with col:
            st.markdown(module_card(title, desc), unsafe_allow_html=True)
            st.page_link(target, label=f"Open {title} →")


# --- Technical readiness (expander) ------------------------------------------

with st.expander("Data readiness & exports (technical)", expanded=False):
    exports = list_parquet_exports()
    tables = duckdb_table_overview()
    db_ready = database_exists()
    ready_expected = int((exports["exists"] & ~exports["optional"]).sum()) if not exports.empty else 0
    expected = int((~exports["optional"]).sum()) if not exports.empty else 0

    cols = st.columns(3)
    cols[0].metric("Required exports", f"{ready_expected}/{expected}")
    cols[1].metric("DuckDB", "Ready" if db_ready else "Missing")
    cols[2].metric("DuckDB tables", human_int(len(tables)) if not tables.empty else "0")

    if not db_ready:
        st.warning(f"DuckDB database not found at `{repo_relative(DB_PATH)}` — official pages fall back to Parquet.")
    if not exports.empty:
        display = exports.copy()
        display["Status"] = [status_label(e, o) for e, o in zip(display["exists"], display["optional"])]
        display["Size"] = display["size_bytes"].map(human_bytes)
        display["Modified"] = display["modified"].map(human_datetime)
        st.dataframe(
            display[["Status", "label", "file", "Size", "Modified"]].rename(
                columns={"label": "Dataset", "file": "File"}),
            hide_index=True, width="stretch",
        )
    caption(
        f"Exports live in `{repo_relative(APP_DATA_DIR)}`. Rebuild with "
        "`python scripts/10_export_dashboard_data.py`. The dashboard is read-only: it never writes to "
        "paper tables, official regime labels, bootstrap, or Forbes–Rigobon result files."
    )
