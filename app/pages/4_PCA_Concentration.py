"""PCA Concentration — does the universe collapse onto fewer risk directions?"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from app.utils.components import caption, interpretation_panel, page_header, section, stat_card, stat_row  # noqa: E402
from app.utils.constants import UNIVERSE_LABELS, UNIVERSES  # noqa: E402
from app.utils.datasets import load_pca_comparison, load_pca_eigenvalues, load_pca_summary  # noqa: E402
from app.utils.plotting import base_layout, calm_stress_bars, style_axes  # noqa: E402
from app.utils.theme import PALETTE, SEMANTIC, configure_page  # noqa: E402

configure_page("PCA Concentration")

summary = load_pca_summary()
eigen = load_pca_eigenvalues()
comparison = load_pca_comparison()
if summary.empty or eigen.empty:
    page_header("Portfolio-level concentration", "PCA Concentration",
                "PCA outputs are unavailable — export dashboard data first.")
    st.stop()

for df in (summary, eigen):
    df["universe"] = df["universe"].astype(str)
    df["regime"] = df["regime"].astype(str)

page_header(
    "Result 2 · Principal-component concentration",
    "Does the asset universe collapse onto fewer independent risk directions?",
    "Eigendecomposition of the official regime-conditional correlation matrices. A universe is more "
    "concentrated in stress when the leading component (PC1 share) rises and the effective number of bets falls.",
    provenance="official",
)

universe_order = [u for u in UNIVERSES if u in set(summary["universe"])]
with st.sidebar:
    st.header("Controls")
    universe = st.selectbox("Universe", universe_order, format_func=lambda u: UNIVERSE_LABELS.get(u, u))

sub_sum = summary[(summary["universe"] == universe) & (summary["regime"].isin(["calm", "stress"]))]
calm = sub_sum[sub_sum["regime"] == "calm"].iloc[0]
stress = sub_sum[sub_sum["regime"] == "stress"].iloc[0]
pc1_d = stress["pc1_share"] - calm["pc1_share"]
neff_d = stress["effective_bets"] - calm["effective_bets"]
concentrates = pc1_d > 0 and neff_d < 0

stat_row([
    stat_card("PC1 share · calm", f"{calm['pc1_share'] * 100:.1f}%"),
    stat_card("PC1 share · stress", f"{stress['pc1_share'] * 100:.1f}%",
              delta=f"{pc1_d * 100:+.1f} pp", delta_color=(SEMANTIC["stress"] if pc1_d > 0 else SEMANTIC["calm"])),
    stat_card("Effective bets · calm", f"{calm['effective_bets']:.2f}"),
    stat_card("Effective bets · stress", f"{stress['effective_bets']:.2f}",
              delta=f"{neff_d:+.2f}", delta_color=(SEMANTIC["stress"] if neff_d < 0 else SEMANTIC["calm"]),
              sub="Lower = more concentrated"),
])

section("Concentration verdict")
left, right = st.columns([1, 1])
with left:
    st.plotly_chart(
        calm_stress_bars(["PC1 share"], [calm["pc1_share"]], [stress["pc1_share"]],
                         value_fmt=".1%", tickformat=".0%", yaxis_title="Leading-component share",
                         title="Variance on the leading component", height=340, hover_suffix=""),
        width="stretch")
with right:
    st.plotly_chart(
        calm_stress_bars(["Effective bets"], [calm["effective_bets"]], [stress["effective_bets"]],
                         value_fmt=".2f", yaxis_title="Effective number of bets",
                         title="Independent bets retained", height=340),
        width="stretch")

verdict = ("more concentrated in stress" if concentrates else "not uniformly more concentrated in stress")
paras = [
    f"In <b>{UNIVERSE_LABELS.get(universe, universe)}</b> the leading component absorbs "
    f"<b>{calm['pc1_share'] * 100:.0f}%</b> of variance in calm and <b>{stress['pc1_share'] * 100:.0f}%</b> in stress, "
    f"while the effective number of bets moves from <b>{calm['effective_bets']:.2f}</b> to "
    f"<b>{stress['effective_bets']:.2f}</b>.",
    f"PC1 share {'rises' if pc1_d > 0 else 'falls'} and effective bets {'fall' if neff_d < 0 else 'rise'}, so this "
    f"universe is <b>{verdict}</b>: returns {'load onto fewer independent directions' if concentrates else 'do not clearly compress'} "
    f"exactly when diversification is most needed.",
    "PC1 share and effective bets are two summaries of the same eigenvalue spectrum, so they move together by "
    "construction; read them as one concentration finding, not two independent confirmations.",
]
interpretation_panel(paras, title="Concentration verdict")

# --- Spectra ------------------------------------------------------------------
section("Eigenvalue spectrum and cumulative variance")
sub_eig = eigen[(eigen["universe"] == universe) & (eigen["regime"].isin(["calm", "stress"]))]
fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.11,
                    subplot_titles=("Eigenvalue spectrum", "Cumulative explained variance"))
for regime, color in [("calm", SEMANTIC["calm"]), ("stress", SEMANTIC["stress"])]:
    rd = sub_eig[sub_eig["regime"] == regime]
    fig.add_trace(go.Scatter(x=rd["component"], y=rd["eigenvalue"], mode="lines+markers",
                             name=regime.title(), line=dict(color=color, width=2), marker=dict(size=6),
                             hovertemplate="PC%{x} · eigenvalue %{y:.3f}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=rd["component"], y=rd["cumulative_explained_variance_share"], mode="lines+markers",
                             line=dict(color=color, width=2), marker=dict(size=6), showlegend=False,
                             hovertemplate="PC%{x} · cumulative %{y:.1%}<extra></extra>"), row=1, col=2)
fig.add_hline(y=1.0, line_color=PALETTE["text_faint"], line_dash="dot", line_width=1, row=1, col=1)
fig.update_yaxes(title_text="Eigenvalue", row=1, col=1)
fig.update_yaxes(title_text="Cumulative share", tickformat=".0%", range=[0, 1.03], row=1, col=2)
fig.update_xaxes(title_text="Principal component", dtick=1)
fig.update_layout(**base_layout(400, legend=True, hovermode="x unified"))
style_axes(fig)
st.plotly_chart(fig, width="stretch")
caption("An eigenvalue above 1 (dotted line) marks a component explaining more than one asset's worth of variance.")

if not comparison.empty:
    section("Cross-universe comparison")
    comp = comparison.copy()
    comp["label"] = comp["universe"].map(lambda u: UNIVERSE_LABELS.get(u, u))
    fig2 = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                         subplot_titles=("Δ PC1 share (stress − calm)", "Δ effective bets (stress − calm)"))
    fig2.add_trace(go.Bar(x=comp["label"], y=comp["stress_minus_calm_pc1_share"],
                          marker_color=[SEMANTIC["stress"] if v > 0 else SEMANTIC["calm"]
                                        for v in comp["stress_minus_calm_pc1_share"]], showlegend=False,
                          hovertemplate="%{x}<br>ΔPC1: %{y:.1%}<extra></extra>"), row=1, col=1)
    fig2.add_trace(go.Bar(x=comp["label"], y=comp["stress_minus_calm_effective_bets"],
                          marker_color=[SEMANTIC["stress"] if v < 0 else SEMANTIC["calm"]
                                        for v in comp["stress_minus_calm_effective_bets"]], showlegend=False,
                          hovertemplate="%{x}<br>ΔNeff: %{y:.2f}<extra></extra>"), row=1, col=2)
    fig2.update_yaxes(tickformat=".0%", row=1, col=1)
    fig2.update_xaxes(tickangle=-12)
    fig2.update_layout(**base_layout(340))
    style_axes(fig2)
    st.plotly_chart(fig2, width="stretch")
    caption("Every universe sits in the concentration quadrant: PC1 share up, effective bets down.")

# --- Rolling concentration (optional exploratory diagnostic) -------------------
from app.utils.datasets import load_rolling_absorption, official_stress_spans  # noqa: E402
from app.utils.plotting import add_stress_bands, finalize  # noqa: E402

rolling = load_rolling_absorption()
if not rolling.empty and "pc1_share" in rolling.columns:
    rpath = rolling[rolling["universe"] == universe].sort_values("date")
    if not rpath.empty:
        section("Rolling concentration through time (absorption ratio)")
        fig3 = go.Figure()
        add_stress_bands(fig3, official_stress_spans())
        fig3.add_trace(go.Scatter(
            x=rpath["date"], y=rpath["pc1_share"], mode="lines",
            line=dict(color=PALETTE["text"], width=1.4), name="126-day PC1 share",
            hovertemplate="%{x|%Y-%m-%d}<br>Rolling PC1 share: %{y:.1%}<extra></extra>"))
        for value, color, label in [(calm["pc1_share"], SEMANTIC["calm"], "Official calm"),
                                    (stress["pc1_share"], SEMANTIC["stress"], "Official stress")]:
            fig3.add_hline(y=value, line_color=color, line_dash="dash", line_width=1.2,
                           annotation_text=f"{label} {value:.0%}", annotation_position="right",
                           annotation_font=dict(size=10, color=color))
        finalize(fig3, 340, yaxis_title="Rolling PC1 share",
                 margin=dict(l=48, r=105, t=24, b=36))
        fig3.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig3, width="stretch")
        caption("Exploratory 126-day rolling leading-component share — the 'absorption ratio' of Kritzman & Li "
                "(2011). Shaded bands are official Markov stress periods: concentration spikes line up with "
                "stress arrivals, giving the static calm/stress comparison its time dimension.")
