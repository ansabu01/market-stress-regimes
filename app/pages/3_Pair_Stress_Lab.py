"""Pair Stress Lab — one pair: raw change, bootstrap significance, adjustment."""

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
from app.utils.constants import FR_METHOD_LABELS, UNIVERSE_LABELS, UNIVERSES  # noqa: E402
from app.utils.datasets import load_bootstrap_pairs, load_fr_pairs  # noqa: E402
from app.utils.plotting import base_layout, style_axes  # noqa: E402
from app.utils.theme import FR_CLASS_COLORS, PALETTE, SEMANTIC, configure_page  # noqa: E402

configure_page("Pair Stress Lab")

boot = load_bootstrap_pairs()
fr = load_fr_pairs()
if boot.empty:
    page_header("Pair-level inference", "Pair Stress Lab",
                "Bootstrap pair results are unavailable — export dashboard data first.")
    st.stop()

for col in ["corr_calm", "corr_stress", "delta_corr", "ci_low", "ci_high", "p_boot_two_sided", "q_value_bh"]:
    boot[col] = pd.to_numeric(boot[col], errors="coerce")
boot["pair"] = boot["asset_i"] + "–" + boot["asset_j"]
boot["key"] = boot[["asset_i", "asset_j"]].apply(lambda r: "|".join(sorted(r)), axis=1)
if not fr.empty:
    for col in ["delta_corr", "delta_corr_adjusted", "corr_stress_adjusted", "fr_delta_used"]:
        fr[col] = pd.to_numeric(fr[col], errors="coerce")
    fr["key"] = fr[["asset_i", "asset_j"]].apply(lambda r: "|".join(sorted(r)), axis=1)

page_header(
    "Result 1 + 3 · Pair-level diagnosis",
    "Is a single pair's stress change real — and does it survive adjustment?",
    "Precomputed block-bootstrap inference (B = 2,000, 21-day blocks) and Forbes–Rigobon adjustment for one "
    "asset pair. Bootstrap p-values and FDR q-values are the official ones; they are never recomputed for custom samples.",
    provenance="official",
)

universe_order = [u for u in UNIVERSES if u in set(boot["universe"])]
with st.sidebar:
    st.header("Filters")
    universe = st.selectbox("Universe", universe_order, format_func=lambda u: UNIVERSE_LABELS.get(u, u))
    uboot = boot[boot["universe"] == universe].copy()
    fdr = st.selectbox("Significance", ["All pairs", "FDR significant (q<0.05)", "Not FDR significant"])
    direction = st.multiselect("Direction", sorted(uboot["direction"].dropna().unique()))
    assets = sorted(set(uboot["asset_i"]) | set(uboot["asset_j"]))
    asset_filter = st.multiselect("Contains asset", assets)

view = uboot.copy()
if fdr.startswith("FDR"):
    view = view[view["significant_fdr_05"].astype(bool)]
elif fdr.startswith("Not"):
    view = view[~view["significant_fdr_05"].astype(bool)]
if direction:
    view = view[view["direction"].isin(direction)]
if asset_filter:
    view = view[view["asset_i"].isin(asset_filter) | view["asset_j"].isin(asset_filter)]
if view.empty:
    st.warning("No pairs match the selected filters.")
    st.stop()

view = view.sort_values("delta_corr", key=lambda s: s.abs(), ascending=False)
view["opt"] = view["pair"] + "   (Δ " + view["delta_corr"].map(lambda v: f"{v:+.3f}") + ")"
selected = st.selectbox("Selected pair", view["opt"].tolist())
row = view[view["opt"] == selected].iloc[0]

# FR rows for this pair
fr_rows = fr[(fr["universe"] == universe) & (fr["key"] == row["key"])] if not fr.empty else pd.DataFrame()
market = fr_rows[fr_rows["fr_method"] == "market_spy"]
pairmax = fr_rows[fr_rows["fr_method"] == "pair_max"]

# --- Headline classification chip ---------------------------------------------
sig = bool(row["significant_fdr_05"])
dir_label = {"increase": "Significant increase", "decrease": "Significant decrease",
             "inconclusive": "Not distinguishable from zero"}.get(row["direction"], row["direction"])
chip_color = SEMANTIC["stress"] if row["direction"] == "increase" else (
    SEMANTIC["resilient"] if row["direction"] == "decrease" else SEMANTIC["inconclusive"])
st.markdown(
    f'<div style="margin:0.3rem 0 0.2rem 0"><span class="ds-chip" '
    f'style="background:{chip_color}22;color:{chip_color};border:1px solid {chip_color}55">'
    f'{row["pair"]} · {dir_label}{" · FDR significant" if sig else ""}</span></div>',
    unsafe_allow_html=True)

ci_txt = (f"[{row['ci_low']:+.3f}, {row['ci_high']:+.3f}]"
          if pd.notna(row["ci_low"]) else "—")
stat_row([
    stat_card("Calm correlation", f"{row['corr_calm']:+.3f}"),
    stat_card("Stress correlation", f"{row['corr_stress']:+.3f}",
              delta=f"{row['delta_corr']:+.3f}",
              delta_color=(SEMANTIC["stress"] if row["delta_corr"] > 0 else SEMANTIC["calm"])),
    stat_card("Bootstrap 95% CI", ci_txt, sub="Excludes 0 → significant" if sig else "Includes 0"),
    stat_card("Bootstrap p / BH q", f"{row['p_boot_two_sided']:.3f} / {row['q_value_bh']:.3f}",
              sub="Two-sided · FDR-adjusted"),
])

# --- Visual hierarchy: calm→stress + bootstrap CI + FR ------------------------
c_left, c_mid, c_right = st.columns(3)

with c_left:
    section("Calm → stress")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=["Calm", "Stress"], y=[row["corr_calm"], row["corr_stress"]],
                             mode="lines+markers+text", line=dict(color=PALETTE["text_faint"], width=2),
                             marker=dict(size=16, color=[SEMANTIC["calm"], SEMANTIC["stress"]],
                                         line=dict(width=1, color=PALETTE["bg"])),
                             text=[f"{row['corr_calm']:+.2f}", f"{row['corr_stress']:+.2f}"],
                             textposition="top center", textfont=dict(color=PALETTE["text"]), showlegend=False,
                             hovertemplate="%{x}: %{y:+.3f}<extra></extra>"))
    fig.add_hline(y=0, line_color=PALETTE["text_faint"], line_dash="dot", line_width=1)
    fig.update_layout(**base_layout(300, yaxis_title="Correlation"))
    style_axes(fig)
    st.plotly_chart(fig, width="stretch")

with c_mid:
    section("Δ with bootstrap interval")
    fig = go.Figure()
    if pd.notna(row["ci_low"]):
        fig.add_trace(go.Scatter(x=[row["ci_low"], row["ci_high"]], y=["Δ", "Δ"], mode="lines",
                                 line=dict(color=SEMANTIC["mostly_resilient"], width=9), showlegend=False,
                                 hovertemplate="CI bound: %{x:+.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[row["delta_corr"]], y=["Δ"], mode="markers",
                             marker=dict(size=16, color=SEMANTIC["stress"] if row["delta_corr"] > 0 else SEMANTIC["calm"],
                                         line=dict(width=1, color=PALETTE["bg"])), showlegend=False,
                             hovertemplate="Δ = %{x:+.3f}<extra></extra>"))
    fig.add_vline(x=0, line_color=PALETTE["text_faint"], line_dash="dash", line_width=1)
    fig.update_layout(**base_layout(300, xaxis_title="Stress − calm correlation", margin=dict(l=30, r=20, t=30, b=44)))
    style_axes(fig)
    fig.update_yaxes(showticklabels=False)
    st.plotly_chart(fig, width="stretch")

with c_right:
    section("Raw → adjusted (Forbes–Rigobon)")
    if fr_rows.empty:
        st.info("No Forbes–Rigobon adjustment stored for this pair.")
    else:
        labels, vals, colors = ["Raw Δ"], [row["delta_corr"]], [PALETTE["neutral"] if False else SEMANTIC["neutral"]]
        for method_key, grp in [("market_spy", market), ("pair_max", pairmax)]:
            if not grp.empty:
                labels.append(FR_METHOD_LABELS[method_key].split(" (")[0])
                v = grp.iloc[0]["delta_corr_adjusted"]
                vals.append(v)
                colors.append(FR_CLASS_COLORS.get(grp.iloc[0]["interpretation"], SEMANTIC["inconclusive"]))
        fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=colors,
                               text=[f"{v:+.2f}" for v in vals], textposition="outside",
                               textfont=dict(color=PALETTE["text_muted"], size=10),
                               hovertemplate="%{x}: %{y:+.3f}<extra></extra>"))
        fig.add_hline(y=0.10, line_color=PALETTE["text_faint"], line_dash="dot", line_width=1,
                      annotation_text="0.10 breakdown", annotation_font=dict(size=9, color=PALETTE["text_faint"]))
        fig.add_hline(y=0, line_color=PALETTE["text_faint"], line_width=1)
        fig.update_layout(**base_layout(300, yaxis_title="Δ correlation"))
        style_axes(fig)
        st.plotly_chart(fig, width="stretch")

# --- Deterministic interpretation ---------------------------------------------
section("Interpretation")
paras = []
verb = "rises" if row["delta_corr"] > 0 else "falls"
paras.append(f"In stress, <b>{row['pair']}</b> {verb} from <b>{row['corr_calm']:+.2f}</b> to "
             f"<b>{row['corr_stress']:+.2f}</b> (Δ {row['delta_corr']:+.3f}).")
if pd.notna(row["ci_low"]):
    if sig:
        paras.append(f"The 95% bootstrap interval <b>{ci_txt}</b> excludes zero and the BH q-value is "
                     f"<b>{row['q_value_bh']:.3f}</b>, so the change is statistically credible after "
                     f"controlling the false-discovery rate — respecting the serial dependence of daily returns.")
    else:
        paras.append(f"The 95% bootstrap interval <b>{ci_txt}</b> includes zero (p = {row['p_boot_two_sided']:.2f}), "
                     f"so the observed change is <b>not distinguishable</b> from sampling variation under this design.")
if not market.empty:
    m = market.iloc[0]
    paras.append(f"Under the SPY market-shock adjustment the change becomes <b>{m['delta_corr_adjusted']:+.3f}</b> — "
                 f"classified <b>{m['interpretation']}</b>. "
                 + ("The rise is largely mechanical: it reflects higher common-factor volatility rather than a "
                    "structural change in dependence, though the experienced co-movement is still real."
                    if "Volatility" in m["interpretation"] else
                    "The relationship is comparatively resilient to the volatility correction."))
elif not pairmax.empty:
    m = pairmax.iloc[0]
    paras.append(f"Under the conservative pair-max adjustment the change becomes <b>{m['delta_corr_adjusted']:+.3f}</b>, "
                 f"classified <b>{m['interpretation']}</b>.")
interpretation_panel(paras)

# --- Rolling correlation path (optional exploratory diagnostic) ----------------
from app.utils.datasets import load_rolling_pairs, official_stress_spans  # noqa: E402
from app.utils.plotting import add_stress_bands, finalize  # noqa: E402

rolling = load_rolling_pairs()
if not rolling.empty:
    rkey = rolling[["asset_i", "asset_j"]].apply(lambda r: "|".join(sorted(r)), axis=1)
    rpath = rolling[(rolling["universe"] == universe) & (rkey == row["key"])].sort_values("date")
    if not rpath.empty:
        section("Rolling correlation through time")
        fig = go.Figure()
        add_stress_bands(fig, official_stress_spans())
        fig.add_trace(go.Scatter(
            x=rpath["date"], y=rpath["rolling_correlation"], mode="lines",
            line=dict(color=PALETTE["text"], width=1.4), name="126-day rolling",
            hovertemplate="%{x|%Y-%m-%d}<br>126-day correlation: %{y:+.3f}<extra></extra>"))
        for value, color, label in [(row["corr_calm"], SEMANTIC["calm"], "Official calm"),
                                    (row["corr_stress"], SEMANTIC["stress"], "Official stress")]:
            fig.add_hline(y=value, line_color=color, line_dash="dash", line_width=1.2,
                          annotation_text=f"{label} {value:+.2f}",
                          annotation_position="right",
                          annotation_font=dict(size=10, color=color))
        fig.add_hline(y=0, line_color=PALETTE["text_faint"], line_width=1)
        finalize(fig, 340, yaxis_title=f"{row['pair']} correlation",
                 margin=dict(l=48, r=110, t=24, b=36))
        st.plotly_chart(fig, width="stretch")
        caption("Exploratory 126-day rolling Pearson correlation (precomputed diagnostic). Shaded bands are "
                "official Markov stress periods; dashed lines are the official regime-conditional correlations. "
                "For SPY–TLT the 2022 sign flip is visible to the naked eye.")

section("Pair ranking (filtered)")
tbl = view[["pair", "corr_calm", "corr_stress", "delta_corr", "ci_low", "ci_high",
            "p_boot_two_sided", "q_value_bh", "significant_fdr_05", "direction"]].head(40)
st.dataframe(tbl, hide_index=True, width="stretch", column_config={
    "pair": st.column_config.TextColumn("Pair"),
    "corr_calm": st.column_config.NumberColumn("Calm", format="%.3f"),
    "corr_stress": st.column_config.NumberColumn("Stress", format="%.3f"),
    "delta_corr": st.column_config.NumberColumn("Δ", format="%+.3f"),
    "ci_low": st.column_config.NumberColumn("CI low", format="%+.3f"),
    "ci_high": st.column_config.NumberColumn("CI high", format="%+.3f"),
    "p_boot_two_sided": st.column_config.NumberColumn("p", format="%.3f"),
    "q_value_bh": st.column_config.NumberColumn("q (BH)", format="%.3f"),
    "significant_fdr_05": st.column_config.CheckboxColumn("FDR 5%"),
    "direction": st.column_config.TextColumn("Direction")})
caption("Bootstrap CIs, p-values, and FDR q-values are the official precomputed values for the paper's balanced sample.")
