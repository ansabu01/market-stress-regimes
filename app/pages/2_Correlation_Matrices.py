"""Correlation Matrices — which relationships tighten or decouple in stress?"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from app.utils.components import caption, interpretation_panel, page_header, section, stat_card, stat_row  # noqa: E402
from app.utils.constants import UNIVERSE_LABELS, UNIVERSES  # noqa: E402
from app.utils.datasets import load_corr_pairs  # noqa: E402
from app.utils.plotting import correlation_heatmap  # noqa: E402
from app.utils.theme import PALETTE, SEMANTIC, configure_page  # noqa: E402

configure_page("Correlation Matrices")

pairs = load_corr_pairs()
if pairs.empty:
    page_header("Regime-conditional dependence", "Correlation Matrices",
                "Stored pair correlations are unavailable — export dashboard data first.")
    st.stop()

page_header(
    "Result 1 · Regime-conditional correlations",
    "Which relationships tighten or decouple when stress arrives?",
    "Official Pearson correlations on calm vs stress days, reconstructed from the stored pipeline "
    "pair table. Positive stress-minus-calm change (orange) = tighter co-movement; negative (blue) = decoupling.",
    provenance="official",
)

universe_order = [u for u in UNIVERSES if u in set(pairs["universe"])]
with st.sidebar:
    st.header("Controls")
    universe = st.selectbox("Universe", universe_order,
                            format_func=lambda u: UNIVERSE_LABELS.get(u, u))
    view_mode = st.radio("View", ["Side by side", "Calm", "Stress", "Difference"], index=0)
    show_values = st.checkbox("Show values", value=True)

sub = pairs[pairs["universe"] == universe]
assets = [a for a in UNIVERSES[universe] if a in set(sub["asset_i"]) | set(sub["asset_j"])]


def matrix(regime: str, diagonal: float) -> pd.DataFrame:
    m = pd.DataFrame(np.nan, index=assets, columns=assets, dtype=float)
    for a in assets:
        m.loc[a, a] = diagonal
    for row in sub[sub["regime"] == regime].itertuples(index=False):
        if row.asset_i in assets and row.asset_j in assets:
            m.loc[row.asset_i, row.asset_j] = row.correlation
            m.loc[row.asset_j, row.asset_i] = row.correlation
    return m


calm, stress = matrix("calm", 1.0), matrix("stress", 1.0)
delta = stress - calm
for a in assets:
    delta.loc[a, a] = 0.0

# --- Pair-level change table (drives metrics + interpretation) ----------------
rows = []
for i, ai in enumerate(assets):
    for aj in assets[i + 1:]:
        d = delta.loc[ai, aj]
        if pd.notna(d):
            rows.append({"pair": f"{ai}–{aj}", "asset_i": ai, "asset_j": aj,
                         "calm": calm.loc[ai, aj], "stress": stress.loc[ai, aj], "delta": d})
changes = pd.DataFrame(rows)
avg_calm = changes["calm"].mean()
avg_stress = changes["stress"].mean()
n_tighten = int((changes["delta"] >= 0.10).sum())
n_decouple = int((changes["delta"] < 0).sum())

stat_row([
    stat_card("Avg correlation · calm", f"{avg_calm:.3f}", sub=f"{len(assets)} assets · {len(changes)} pairs"),
    stat_card("Avg correlation · stress", f"{avg_stress:.3f}",
              delta=f"{avg_stress - avg_calm:+.3f}",
              delta_color=(SEMANTIC["stress"] if avg_stress > avg_calm else SEMANTIC["calm"]),
              sub="Mean pairwise Pearson"),
    stat_card("Breakdown pairs", f"{n_tighten}", sub="Δρ ≥ +0.10 (tighten in stress)"),
    stat_card("Resilient pairs", f"{n_decouple}", sub="Δρ < 0 (decouple in stress)"),
])

section("Correlation structure by regime")
if view_mode == "Side by side":
    # In the 3-up view, cell labels are unreadable beyond a small universe; rely on
    # color + hover there and keep numbers only when the checkbox is on and it fits.
    compact_values = show_values and len(assets) <= 6
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(correlation_heatmap(calm, title="Calm", height=430, show_values=compact_values),
                        width="stretch")
    with c2:
        st.plotly_chart(correlation_heatmap(stress, title="Stress", height=430, show_values=compact_values),
                        width="stretch")
    with c3:
        bound = max(float(np.nanmax(np.abs(delta.to_numpy()))), 0.05)
        st.plotly_chart(correlation_heatmap(delta, title="Stress − calm", zmin=-bound, zmax=bound,
                                            value_label="Δ correlation", height=430, show_values=compact_values),
                        width="stretch")
    if not compact_values and show_values:
        caption("Values hidden in the 3-up view for readability — hover any cell, or pick a single matrix to see numbers.")
else:
    if view_mode == "Difference":
        bound = max(float(np.nanmax(np.abs(delta.to_numpy()))), 0.05)
        fig = correlation_heatmap(delta, title="Stress − calm correlation change",
                                  zmin=-bound, zmax=bound, value_label="Δ correlation",
                                  height=560, show_values=show_values)
    else:
        m = calm if view_mode == "Calm" else stress
        fig = correlation_heatmap(m, title=f"{view_mode} correlations", height=560, show_values=show_values)
    st.plotly_chart(fig, width="stretch")
caption("Diagonal set to 1 (levels) / 0 (difference). Off-diagonal values come from the official correlation_pairs table.")

# --- Largest changes + interpretation -----------------------------------------
left, right = st.columns([1.25, 1])
with left:
    section("Largest correlation changes")
    top = changes.reindex(changes["delta"].abs().sort_values(ascending=False).index).head(12)
    st.dataframe(top[["pair", "calm", "stress", "delta"]], hide_index=True, width="stretch",
                 column_config={"pair": st.column_config.TextColumn("Pair"),
                                "calm": st.column_config.NumberColumn("Calm", format="%.3f"),
                                "stress": st.column_config.NumberColumn("Stress", format="%.3f"),
                                "delta": st.column_config.NumberColumn("Δ (stress − calm)", format="%+.3f")})
with right:
    section("Reading the change")
    top_up = changes.nlargest(1, "delta").iloc[0] if not changes.empty else None
    top_dn = changes.nsmallest(1, "delta").iloc[0] if not changes.empty else None
    if avg_stress - avg_calm >= 0.05:
        story = (f"The whole panel shifts up: average correlation rises from <b>{avg_calm:.2f}</b> to "
                 f"<b>{avg_stress:.2f}</b>, so co-movement broadly tightens in stress.")
    elif avg_stress - avg_calm <= -0.01:
        story = (f"The average is nearly flat (even falling, {avg_calm:.2f} → {avg_stress:.2f}), yet the "
                 f"structure reshuffles — some pairs tighten sharply while hedges decouple further.")
    else:
        story = (f"The average barely moves ({avg_calm:.2f} → {avg_stress:.2f}); the action is in the "
                 f"cross-section rather than the mean.")
    paras = [story]
    if top_up is not None:
        paras.append(f"Largest tightening: <b>{top_up['pair']}</b> ({top_up['calm']:+.2f} → {top_up['stress']:+.2f}, "
                     f"Δ {top_up['delta']:+.2f}).")
    if top_dn is not None and top_dn["delta"] < 0:
        paras.append(f"Largest decoupling: <b>{top_dn['pair']}</b> ({top_dn['calm']:+.2f} → {top_dn['stress']:+.2f}, "
                     f"Δ {top_dn['delta']:+.2f}) — diversification that survives stress.")
    paras.append("Whether these increases are structural or volatility-driven is tested on the "
                 "<b>Forbes–Rigobon</b> page; their statistical significance on the <b>Pair Stress Lab</b>.")
    interpretation_panel(paras)
