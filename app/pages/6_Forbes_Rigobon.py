"""Forbes-Rigobon — do raw correlation increases survive volatility adjustment?"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from app.utils.components import caption, interpretation_panel, page_header, section, stat_card, stat_row  # noqa: E402
from app.utils.constants import (  # noqa: E402
    FR_CLASS_ORDER, FR_METHOD_LABELS, FR_ROBUST, FR_VOL_SENSITIVE, UNIVERSE_LABELS, UNIVERSES,
)
from app.utils.datasets import load_fr_pairs, load_fr_summary  # noqa: E402
from app.utils.plotting import base_layout, style_axes  # noqa: E402
from app.utils.theme import FR_CLASS_COLORS, PALETTE, SEMANTIC, configure_page  # noqa: E402

configure_page("Forbes-Rigobon")

fr = load_fr_pairs()
summary = load_fr_summary()
if fr.empty:
    page_header("Volatility adjustment", "Forbes–Rigobon",
                "Forbes–Rigobon results are unavailable — export dashboard data first.")
    st.stop()

for col in ["delta_corr", "delta_corr_adjusted", "corr_stress_adjusted", "fr_delta_used"]:
    fr[col] = pd.to_numeric(fr[col], errors="coerce")
fr["pair"] = fr["asset_i"] + "–" + fr["asset_j"]

page_header(
    "Result 3 · Forbes–Rigobon adjustment",
    "Do raw correlation increases survive adjustment for higher volatility?",
    "Raw correlation is the co-movement an investor actually experiences. The adjustment asks whether that "
    "rise reflects a structural change in dependence (contagion) or higher common-factor volatility (interdependence).",
    provenance="official",
)

universe_order = [u for u in UNIVERSES if u in set(fr["universe"])]
with st.sidebar:
    st.header("Controls")
    universe = st.selectbox("Universe", universe_order, format_func=lambda u: UNIVERSE_LABELS.get(u, u))
    ufr = fr[fr["universe"] == universe]
    methods = [m for m in ["market_spy", "pair_max"] if m in set(ufr["fr_method"])]
    method = st.radio("Adjustment method", methods, format_func=lambda m: FR_METHOD_LABELS.get(m, m))
    view = ufr[ufr["fr_method"] == method].copy()
    classes = st.multiselect("Fragility class", sorted(view["interpretation"].unique()))
if classes:
    view = view[view["interpretation"].isin(classes)]
if view.empty:
    st.warning("No rows match the selected filters.")
    st.stop()

robust = int((view["interpretation"] == FR_ROBUST).sum())
vol_sens = int((view["interpretation"] == FR_VOL_SENSITIVE).sum())
avg_raw = view["delta_corr"].mean()
avg_adj = view["delta_corr_adjusted"].mean()
stat_row([
    stat_card("Pairs adjusted", f"{len(view)}", sub=FR_METHOD_LABELS.get(method, method)),
    stat_card("Avg raw Δ", f"{avg_raw:+.3f}", sub="Experienced co-movement change"),
    stat_card("Avg adjusted Δ", f"{avg_adj:+.3f}", delta=f"{avg_adj - avg_raw:+.3f}",
              delta_color=SEMANTIC["calm"], sub="After volatility correction"),
    stat_card("Robust breakdowns", f"{robust}",
              sub="Survive adjustment (Δ and adjusted-Δ ≥ 0.10)"),
])

# --- Redesigned raw vs adjusted scatter ---------------------------------------
section("Raw versus adjusted correlation change")
fig = go.Figure()
bounds = pd.concat([view["delta_corr"], view["delta_corr_adjusted"]]).dropna()
lo = min(float(bounds.min()) - 0.04, -0.05)
hi = max(float(bounds.max()) + 0.04, 0.15)
# diagonal + zero + 0.10 thresholds
fig.add_shape(type="line", x0=lo, y0=lo, x1=hi, y1=hi, line=dict(color=PALETTE["text_faint"], dash="dash", width=1))
for v in (0.0, 0.10):
    fig.add_hline(y=v, line_color=PALETTE["border"], line_width=1,
                  line_dash=("solid" if v == 0 else "dot"))
    fig.add_vline(x=v, line_color=PALETTE["border"], line_width=1,
                  line_dash=("solid" if v == 0 else "dot"))
for cls in FR_CLASS_ORDER:
    grp = view[view["interpretation"] == cls]
    if grp.empty:
        continue
    fig.add_trace(go.Scatter(
        x=grp["delta_corr"], y=grp["delta_corr_adjusted"], mode="markers", name=cls,
        marker=dict(size=10, color=FR_CLASS_COLORS.get(cls, SEMANTIC["inconclusive"]),
                    line=dict(width=0.7, color=PALETTE["bg"])),
        customdata=grp[["pair", "source_asset", "fr_delta_used"]],
        hovertemplate="<b>%{customdata[0]}</b><br>Raw Δ: %{x:+.3f}<br>Adjusted Δ: %{y:+.3f}"
                      "<br>Source: %{customdata[1]} · shock δ=%{customdata[2]:.2f}<extra></extra>"))
fig.add_annotation(x=hi, y=0.11, text="Robust-breakdown zone (both ≥ 0.10)", showarrow=False,
                   xanchor="right", font=dict(size=10, color=PALETTE["text_faint"]))
fig.update_layout(**base_layout(540, legend=True,
                                xaxis_title="Raw stress − calm correlation",
                                yaxis_title="Adjusted stress − calm correlation"))
style_axes(fig)
fig.update_xaxes(range=[lo, hi])
fig.update_yaxes(range=[lo, hi], scaleanchor="x", scaleratio=1)
st.plotly_chart(fig, width="stretch")
caption("Points below the dashed 45° line were pulled down by the volatility correction. Only points inside the "
        "top-right block past both dotted 0.10 lines are robust breakdowns.")

# --- Interpretation + composition ---------------------------------------------
left, right = st.columns([1, 1])
with left:
    section("Fragility-class composition")
    counts = view["interpretation"].value_counts().reindex(FR_CLASS_ORDER).dropna()
    fig2 = go.Figure(go.Bar(
        x=counts.values, y=[c.replace(" after adjustment", "") for c in counts.index], orientation="h",
        marker_color=[FR_CLASS_COLORS.get(c, SEMANTIC["inconclusive"]) for c in counts.index],
        text=counts.values, textposition="outside", textfont=dict(color=PALETTE["text_muted"]),
        hovertemplate="%{y}: %{x} pairs<extra></extra>"))
    fig2.update_layout(**base_layout(300, xaxis_title="Pairs", margin=dict(l=8, r=30, t=20, b=36)))
    style_axes(fig2)
    st.plotly_chart(fig2, width="stretch")
with right:
    section("What the adjustment means")
    interpretation_panel([
        f"Under <b>{FR_METHOD_LABELS.get(method, method)}</b>, <b>{robust}</b> of {len(view)} pairs are robust "
        f"breakdowns and <b>{vol_sens}</b> are volatility-bias-sensitive. The average change falls from "
        f"<b>{avg_raw:+.3f}</b> (raw) to <b>{avg_adj:+.3f}</b> (adjusted).",
        "A volatility-driven verdict does <b>not</b> mean the breakdown was fake. The experienced co-movement is "
        "real and unchanged; the adjustment locates its <b>source</b> in higher common-factor volatility "
        "(<b>interdependence</b>) rather than a structural shift in the dependence relationship (<b>contagion</b>).",
        "Resilient pairs (teal) de-correlate further in stress — genuine diversification that strengthens exactly "
        "when it is needed.",
    ])

section("Adjusted pair table")
tbl = view[["pair", "source_asset", "corr_calm", "corr_stress", "delta_corr", "fr_delta_used",
            "corr_stress_adjusted", "delta_corr_adjusted", "interpretation"]].sort_values(
    "delta_corr_adjusted", key=lambda s: s.abs(), ascending=False)
st.dataframe(tbl, hide_index=True, width="stretch", column_config={
    "pair": st.column_config.TextColumn("Pair"),
    "source_asset": st.column_config.TextColumn("Shock source"),
    "corr_calm": st.column_config.NumberColumn("Calm", format="%.3f"),
    "corr_stress": st.column_config.NumberColumn("Stress", format="%.3f"),
    "delta_corr": st.column_config.NumberColumn("Raw Δ", format="%+.3f"),
    "fr_delta_used": st.column_config.NumberColumn("Variance shock δ", format="%.2f"),
    "corr_stress_adjusted": st.column_config.NumberColumn("Adjusted stress", format="%.3f"),
    "delta_corr_adjusted": st.column_config.NumberColumn("Adjusted Δ", format="%+.3f"),
    "interpretation": st.column_config.TextColumn("Fragility class")})
