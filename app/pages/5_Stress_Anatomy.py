"""Stress Anatomy — does diversification behave the same way in every type of stress?

Descriptive episode heterogeneity. Uses the OFFICIAL Markov stress label and
dynamically recomputes descriptive dependence statistics from the stored balanced
return panel. This is NOT formal inference: no p-values, no bootstrap, no causal
claims. Episode correlations are validated against the stored broad-era table.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from app.utils import analytics as A  # noqa: E402
from app.utils.components import caption, interpretation_panel, page_header, section, stat_card, stat_row  # noqa: E402
from app.utils.constants import (  # noqa: E402
    ASSET_ROLE, BROAD_ERAS, DEFAULT_HEDGE_PAIRS, EPISODE_DESCRIPTIONS, MIN_EPISODE_STRESS_DAYS,
    PRIMARY_EPISODES, UNIVERSE_LABELS, UNIVERSES, pretty_pair,
)
from app.utils.datasets import load_balanced  # noqa: E402
from app.utils.plotting import correlation_heatmap, dumbbell  # noqa: E402
from app.utils.theme import PALETTE, SEMANTIC, configure_page  # noqa: E402

configure_page("Stress Anatomy")

ERA_BOUNDS = {name: (lo, hi) for name, lo, hi in BROAD_ERAS}


def era_for(name: str) -> tuple[int, int] | None:
    return None if name == "Pooled stress" else ERA_BOUNDS[name]


bal_full = load_balanced(tuple(UNIVERSES["etf_assets"]))
if bal_full.empty:
    page_header("Descriptive episode heterogeneity", "Stress Anatomy",
                "Return data is unavailable — export dashboard data first.")
    st.stop()

total_stress = int((bal_full["ms_stress"] == 1).sum())

page_header(
    "Nuance · Descriptive episode heterogeneity",
    "Does diversification behave the same way in every type of market stress?",
    "Correlations recomputed on official Markov stress days, split by calendar era. This is descriptive only — "
    "it identifies WHEN markets were stressed, not WHICH macro shock caused it. No inference is performed.",
    provenance="exploratory",
)

with st.sidebar:
    st.header("Controls")
    universe = st.selectbox("Universe", list(UNIVERSES), index=0,
                            format_func=lambda u: UNIVERSE_LABELS.get(u, u))
    episode = st.selectbox("Episode", PRIMARY_EPISODES, index=0,
                           help="Official Markov stress days within a calendar era. 2024–2025 is omitted (too few days).")
    st.caption(EPISODE_DESCRIPTIONS.get(episode, ""))

columns = UNIVERSES[universe]
bal = load_balanced(tuple(columns))
era = era_for(episode)

# --- Episode summary metrics --------------------------------------------------
stats = A.episode_statistics(bal, columns, era, total_stress)
n_days = int(stats["stress_days"])
if n_days < 3:
    st.warning(f"Episode '{episode}' has too few stress days ({n_days}) to summarize.")
    st.stop()
below_floor = n_days < MIN_EPISODE_STRESS_DAYS

stat_row([
    stat_card("Stress days", f"{n_days:,}",
              sub=f"{stats['share_of_stress'] * 100:.1f}% of pooled stress days"
              + (" · below 100-day floor" if below_floor else "")),
    stat_card("Avg correlation", f"{stats['avg_correlation']:+.3f}", sub="Mean pairwise Pearson (stress days)"),
    stat_card("PC1 share", f"{stats['pc1_share'] * 100:.1f}%", sub="Leading-component concentration"),
    stat_card("Effective bets", f"{stats['effective_bets']:.2f}",
              sub=(f"SPY vol {stats.get('spy_vol_annual', float('nan')) * 100:.0f}% ann."
                   if not np.isnan(stats.get("spy_vol_annual", np.nan)) else "Independent directions")),
])
if below_floor:
    st.info(f"'{episode}' contains only {n_days} stress days — shown for completeness but below the report's "
            "100-day reporting floor. Treat with caution.")

# --- Episode correlation matrix -----------------------------------------------
section(f"Correlation on {episode.lower()} days · {UNIVERSE_LABELS.get(universe, universe)}")
try:
    emat = A.episode_correlation(bal, columns, era)
    assert emat.to_numpy()[np.isfinite(emat.to_numpy())].max() <= 1.0 + 1e-9
    st.plotly_chart(correlation_heatmap(emat, height=480, value_label="Correlation"),
                    width="stretch")
    caption("Descriptive Pearson correlation on official Markov stress days within the selected episode.")
except ValueError as exc:
    st.warning(f"Cannot compute the episode correlation matrix: {exc}")

# --- Hedge behaviour across stress types (dumbbell) ---------------------------
section("Hedge behaviour across stress types")
avail_pairs = [(i, j) for i, j in DEFAULT_HEDGE_PAIRS if i in columns and j in columns]
if not avail_pairs:
    st.info("None of the default hedge pairs are in this universe. Try the combined universe or Panel A.")
else:
    series_episodes = ["Pooled stress", "2007-2019", "2020-2021", "2022-2023"]
    ep_colors = {"Pooled stress": SEMANTIC["neutral"], "2007-2019": SEMANTIC["calm"],
                 "2020-2021": SEMANTIC["mostly_resilient"], "2022-2023": SEMANTIC["stress"]}
    labels = [pretty_pair(i, j) for i, j in avail_pairs]
    values_by_series: dict[str, list[float]] = {}
    for ep in series_episodes:
        sub = A.episode_frame(bal, columns, era=era_for(ep))
        values_by_series[ep] = [A.pair_correlation(sub, i, j) for i, j in avail_pairs]
    st.plotly_chart(
        dumbbell(labels, values_by_series, colors=ep_colors,
                 xaxis_title="Correlation on stress days", height=360, xrange=(-0.8, 1.0)),
        width="stretch")
    caption("Each row is a hedge pair; markers show its correlation on stress days within each era. A pair whose "
            "markers straddle zero changes sign across stress types.")

# --- Pair drilldown across episodes -------------------------------------------
section("Pair drilldown across episodes")
all_pairs = [(columns[a], columns[b]) for a in range(len(columns)) for b in range(a + 1, len(columns))]
pair_labels = {pretty_pair(i, j): (i, j) for i, j in all_pairs}
default_idx = list(pair_labels).index("SPY–TLT") if "SPY–TLT" in pair_labels else 0
chosen = st.selectbox("Pair", list(pair_labels), index=default_idx)
pi, pj = pair_labels[chosen]

episodes_grid = ["2007-2019", "2020-2021", "2022-2023"]
drill_rows = []
pooled_val = A.pair_correlation(A.episode_frame(bal, columns, era=None), pi, pj)
for ep in episodes_grid:
    sub = A.episode_frame(bal, columns, era=era_for(ep))
    drill_rows.append({"episode": ep, "days": len(sub), "correlation": A.pair_correlation(sub, pi, pj)})
drill = pd.DataFrame(drill_rows)

import plotly.graph_objects as go  # noqa: E402
from app.utils.plotting import base_layout, style_axes  # noqa: E402

d_left, d_right = st.columns([1.15, 1])
with d_left:
    fig = go.Figure(go.Bar(
        x=drill["episode"], y=drill["correlation"],
        marker_color=[SEMANTIC["stress"] if v > 0 else SEMANTIC["calm"] for v in drill["correlation"].fillna(0)],
        text=[f"{v:+.2f}" if pd.notna(v) else "—" for v in drill["correlation"]], textposition="outside",
        textfont=dict(color=PALETTE["text_muted"]),
        hovertemplate="%{x}<br>Correlation: %{y:+.3f}<extra></extra>"))
    fig.add_hline(y=pooled_val, line_color=PALETTE["text_faint"], line_dash="dash", line_width=1,
                  annotation_text=f"Pooled {pooled_val:+.2f}", annotation_font=dict(size=10, color=PALETTE["text_faint"]))
    fig.add_hline(y=0, line_color=PALETTE["border"], line_width=1)
    fig.update_layout(**base_layout(320, yaxis_title=f"{chosen} correlation"))
    style_axes(fig)
    st.plotly_chart(fig, width="stretch")

# --- Deterministic interpretation --------------------------------------------
with d_right:
    section("Pair verdict")
    vals = drill["correlation"].dropna()
    paras = []
    if len(vals) >= 2:
        signs = set(np.sign(v) for v in vals if abs(v) >= 0.05)
        rng = float(vals.max() - vals.min())
        if len(signs) > 1:
            paras.append(f"<b>{chosen}</b> is <b>episode-dependent</b>: across the qualifying eras its stress "
                         f"correlation ranges from <b>{vals.min():+.2f}</b> to <b>{vals.max():+.2f}</b> and "
                         f"<b>changes sign</b>, so the relationship differs across stress types.")
        elif rng <= 0.15:
            paras.append(f"<b>{chosen}</b> is <b>comparatively stable</b>: it stays within a narrow band "
                         f"[{vals.min():+.2f}, {vals.max():+.2f}] across stress episodes.")
        elif (vals >= 0.10).all():
            paras.append(f"<b>{chosen}</b> shows <b>persistent stress co-movement</b>: it is strongly positive in "
                         f"every qualifying episode ([{vals.min():+.2f}, {vals.max():+.2f}]).")
        elif (vals <= 0.10).all():
            paras.append(f"<b>{chosen}</b> shows <b>persistent diversification</b>: it stays low or negative in "
                         f"every qualifying episode ([{vals.min():+.2f}, {vals.max():+.2f}]).")
        else:
            paras.append(f"<b>{chosen}</b> varies in magnitude across episodes "
                         f"([{vals.min():+.2f}, {vals.max():+.2f}]) without a clean sign change.")
    role_i, role_j = ASSET_ROLE.get(pi, ""), ASSET_ROLE.get(pj, "")
    if "treasury" in (role_i, role_j) and "equity" in (role_i, role_j):
        paras.append("Descriptively, the stock–Treasury hedge is strongest in deflationary-type stress and weakest "
                     "(even positive) in the inflation-driven 2022–2023 episode.")
    elif "gold" in (role_i, role_j):
        paras.append("Gold-linked pairs tend to stay within a comparatively narrow band across episode types.")
    paras.append("This split is <b>descriptive only</b>. It reflects heterogeneity within the selected stress "
                 "episodes and is not causal inference; the Markov label marks when markets were stressed, not why.")
    interpretation_panel(paras, title="Descriptive reading")

section("Episode comparison table")
comp_rows = []
for ep in PRIMARY_EPISODES:
    s = A.episode_statistics(bal, columns, era_for(ep), total_stress)
    comp_rows.append({"episode": ep, "stress_days": int(s["stress_days"]),
                      "share": s["share_of_stress"], "avg_corr": s["avg_correlation"],
                      "pc1_share": s["pc1_share"], "effective_bets": s["effective_bets"]})
comp = pd.DataFrame(comp_rows)
st.dataframe(comp, hide_index=True, width="stretch", column_config={
    "episode": st.column_config.TextColumn("Episode"),
    "stress_days": st.column_config.NumberColumn("Stress days", format="%d"),
    "share": st.column_config.NumberColumn("Share of stress", format="%.1f%%"),
    "avg_corr": st.column_config.NumberColumn("Avg corr", format="%+.3f"),
    "pc1_share": st.column_config.NumberColumn("PC1 share", format="%.1f%%"),
    "effective_bets": st.column_config.NumberColumn("Effective bets", format="%.2f")})
caption("Recomputed live from stored daily returns and the official Markov stress label. Matches the report's "
        "stored broad-era episode table to machine precision (verified in tests).")
