"""Portfolio X-Ray — how does a custom portfolio's diversification change in stress?

A regime-conditional diagnostic (NOT an optimizer, backtest, or recommendation).
Everything is recomputed live from stored daily returns and the official Markov
``ms_stress`` label on the paper's balanced sample.
"""

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

from app.utils import analytics as A  # noqa: E402
from app.utils.components import caption, interpretation_panel, page_header, section, stat_card, stat_row  # noqa: E402
from app.utils.constants import ASSET_LABELS, ASSET_ROLE, DEFAULT_PORTFOLIO  # noqa: E402
from app.utils.datasets import available_assets, load_balanced  # noqa: E402
from app.utils.plotting import (  # noqa: E402
    base_layout, calm_stress_bars, correlation_heatmap, horizontal_grouped, style_axes,
    variance_decomposition_bars,
)
from app.utils.theme import PALETTE, SEMANTIC, configure_page  # noqa: E402

configure_page("Portfolio X-Ray")

assets = available_assets()
if not assets:
    page_header("Regime-conditional diagnostic", "Portfolio X-Ray",
                "Return data is unavailable — export dashboard data first.")
    st.stop()

page_header(
    "Synthesis · Custom regime diagnostic",
    "How does your portfolio's diversification change under stress?",
    "Pick 2–14 ETFs and weights; every diagnostic is recomputed live on the paper's balanced sample, split by "
    "the official Markov calm/stress label. This is a diversification diagnostic — not an optimizer or a recommendation.",
    provenance="exploratory",
)

# --- Asset + weight selection -------------------------------------------------
with st.sidebar:
    st.header("Portfolio")
    default_sel = [a for a in DEFAULT_PORTFOLIO if a in assets] or assets[:5]
    selected = st.multiselect("Assets (2–14)", assets, default=default_sel,
                              format_func=lambda a: ASSET_LABELS.get(a, a))
    weight_mode = st.radio("Weights", ["Equal weight", "Custom weight"], index=0)

if len(selected) < 2:
    st.warning("Select at least two assets to build a portfolio.")
    st.stop()

n = len(selected)
if weight_mode == "Equal weight":
    raw_weights = np.full(n, 1.0 / n)
    weight_note = "Equal weight: 1/N applied to each asset."
else:
    st.markdown('<div class="ds-caption">Edit weights below (long-only). They are normalized to sum to 100%.</div>',
                unsafe_allow_html=True)
    editor_df = pd.DataFrame({"Asset": [ASSET_LABELS.get(a, a) for a in selected],
                              "Weight %": [round(100.0 / n, 2)] * n})
    edited = st.data_editor(editor_df, hide_index=True, width="stretch",
                            disabled=["Asset"], key="weight_editor",
                            column_config={"Weight %": st.column_config.NumberColumn(
                                "Weight %", min_value=0.0, max_value=100.0, step=1.0, format="%.1f")})
    raw = pd.to_numeric(edited["Weight %"], errors="coerce").fillna(0.0).to_numpy()
    if (raw < 0).any():
        st.error("Negative weights are not supported (long-only). Set them to 0 or above.")
        st.stop()
    if raw.sum() <= 0:
        st.error("Weights sum to zero. Enter at least one positive weight.")
        st.stop()
    raw_weights = raw
    weight_note = f"Custom weights entered summing to {raw.sum():.1f}%, normalized to 100%."

weights = A.normalize_weights(raw_weights)
st.caption(weight_note + "  " + " · ".join(f"{a} {w * 100:.0f}%" for a, w in zip(selected, weights)))

# --- Balanced regime data -----------------------------------------------------
bal = load_balanced(tuple(selected))
if bal.empty or (bal["ms_stress"] == 1).sum() < 3 or (bal["ms_stress"] == 0).sum() < 3:
    st.error("Not enough calm/stress observations for the selected assets on the balanced sample.")
    st.stop()

cov_calm = A.covariance_matrix(bal, selected, A.CALM)
cov_stress = A.covariance_matrix(bal, selected, A.STRESS)
corr_calm = A.regime_correlation(bal, selected, A.CALM)
corr_stress = A.regime_correlation(bal, selected, A.STRESS)

vol_calm = A.portfolio_volatility(weights, cov_calm)
vol_stress = A.portfolio_volatility(weights, cov_stress)
avg_calm = A.average_pairwise_correlation(corr_calm)
avg_stress = A.average_pairwise_correlation(corr_stress)
pc1_calm, pc1_stress = A.pc1_share(corr_calm), A.pc1_share(corr_stress)
neff_calm, neff_stress = A.effective_bets(corr_calm), A.effective_bets(corr_stress)
mult = vol_stress / vol_calm if vol_calm > 0 else float("nan")

# --- Primary regime summary ---------------------------------------------------
section("Your portfolio under stress")
st.markdown(
    f'<div class="ds-caption">Balanced sample {bal["date"].min():%Y-%m-%d} → {bal["date"].max():%Y-%m-%d} · '
    f'{int((bal["ms_stress"] == 0).sum()):,} calm / {int((bal["ms_stress"] == 1).sum()):,} stress days.</div>',
    unsafe_allow_html=True)


def change(v_calm, v_stress, fmt, pct=False):
    d = v_stress - v_calm
    txt = f"{d * 100:+.1f} pp" if pct else f"{d:{fmt}}"
    color = SEMANTIC["stress"] if d > 0 else (SEMANTIC["calm"] if d < 0 else PALETTE["text_faint"])
    return txt, color


rows = [
    ("Annualized volatility", f"{vol_calm * 100:.1f}%", f"{vol_stress * 100:.1f}%", change(vol_calm, vol_stress, "+.3f", pct=True)),
    ("Avg pairwise correlation", f"{avg_calm:+.3f}", f"{avg_stress:+.3f}", change(avg_calm, avg_stress, "+.3f")),
    ("PC1 share", f"{pc1_calm * 100:.1f}%", f"{pc1_stress * 100:.1f}%", change(pc1_calm, pc1_stress, "+.3f", pct=True)),
    ("Effective bets", f"{neff_calm:.2f}", f"{neff_stress:.2f}", change(neff_calm, neff_stress, "+.2f")),
]
cards = []
for label, cval, sval, (dtxt, dcol) in rows:
    cards.append(stat_card(label, sval, delta=f"{dtxt} vs calm", delta_color=dcol, sub=f"Calm: {cval}"))
stat_row(cards)

extra = st.columns(2)
with extra[0]:
    st.markdown(stat_card("Stress volatility multiplier", f"{mult:.2f}×",
                          sub="Stress volatility / calm volatility"), unsafe_allow_html=True)
with extra[1]:
    dr_calm, dr_stress = A.diversification_ratio(weights, cov_calm), A.diversification_ratio(weights, cov_stress)
    dtxt, dcol = change(dr_calm, dr_stress, "+.2f")
    st.markdown(stat_card("Diversification ratio", f"{dr_stress:.2f}", delta=f"{dtxt} vs calm",
                          delta_color=(SEMANTIC["calm"] if dr_stress >= dr_calm else SEMANTIC["stress"]),
                          sub=f"Calm: {dr_calm:.2f} · weighted-avg vol / portfolio vol"), unsafe_allow_html=True)

# --- Correlation structure ----------------------------------------------------
section("Correlation structure (selected assets)")
view = st.radio("Matrix", ["Calm", "Stress", "Difference"], index=1, horizontal=True)
if view == "Difference":
    delta = corr_stress - corr_calm
    for a in selected:
        delta.loc[a, a] = 0.0
    bound = max(float(np.nanmax(np.abs(delta.to_numpy()))), 0.05)
    st.plotly_chart(correlation_heatmap(delta, zmin=-bound, zmax=bound, value_label="Δ correlation", height=440),
                    width="stretch")
else:
    st.plotly_chart(correlation_heatmap(corr_calm if view == "Calm" else corr_stress, height=440),
                    width="stretch")
caption("Dynamically recomputed from the selected assets on calm / stress days.")

# --- PCA + concentration ------------------------------------------------------
section("Concentration (PCA)")
pc_left, pc_right = st.columns(2)
with pc_left:
    st.plotly_chart(calm_stress_bars(["PC1 share"], [pc1_calm], [pc1_stress], value_fmt=".1%",
                                     tickformat=".0%", yaxis_title="Leading-component share",
                                     title="PC1 share", height=320), width="stretch")
with pc_right:
    st.plotly_chart(calm_stress_bars(["Effective bets"], [neff_calm], [neff_stress], value_fmt=".2f",
                                     yaxis_title="Effective bets", title="Effective bets", height=320),
                    width="stretch")

# --- Risk contribution --------------------------------------------------------
section("Risk contribution by asset")
rc_calm = A.risk_contributions(weights, cov_calm)
rc_stress = A.risk_contributions(weights, cov_stress)
# validation guards (dev-facing, silent unless broken)
assert np.isclose(rc_calm.component.sum(), rc_calm.portfolio_vol_daily, atol=1e-10)
assert np.isclose(rc_stress.component.sum(), rc_stress.portfolio_vol_daily, atol=1e-10)
order = np.argsort(rc_stress.percent)[::-1]
cats = [selected[i] for i in order]
st.plotly_chart(
    horizontal_grouped(cats, {
        "Calm": ([rc_calm.percent[i] for i in order], SEMANTIC["calm"]),
        "Stress": ([rc_stress.percent[i] for i in order], SEMANTIC["stress"]),
    }, xaxis_title="Share of portfolio volatility", tickformat=".0%", height=max(300, 40 * n)),
    width="stretch")
caption("Component contribution to risk: CCR_i = w_i · (Σw)_i / σ_p. Contributions sum to portfolio volatility "
        "(Euler decomposition). Bars show each asset's share of total portfolio volatility, by regime.")

# --- Variance decomposition ---------------------------------------------------
section("Variance decomposition: own-variance vs covariance")
vd_calm = A.variance_decomposition(weights, cov_calm)
vd_stress = A.variance_decomposition(weights, cov_stress)
assert np.isclose(vd_calm.portfolio_variance, vd_calm.diagonal + vd_calm.off_diagonal, atol=1e-14)
assert np.isclose(vd_stress.portfolio_variance, vd_stress.diagonal + vd_stress.off_diagonal, atol=1e-14)
vdec_left, vdec_right = st.columns([1.1, 1])
with vdec_left:
    st.plotly_chart(
        variance_decomposition_bars((vd_calm.diagonal, vd_calm.off_diagonal),
                                    (vd_stress.diagonal, vd_stress.off_diagonal), height=320),
        width="stretch")
with vdec_right:
    st.markdown(
        f'<div class="ds-caption">Portfolio variance = own-variance (diagonal) + covariance (off-diagonal). '
        f'The covariance term is the diversification channel and can be negative when hedges offset.<br><br>'
        f'<b style="color:{PALETTE["text"]}">Calm</b>: covariance is '
        f'{vd_calm.diversification_share * 100:+.0f}% of portfolio variance.<br>'
        f'<b style="color:{PALETTE["text"]}">Stress</b>: covariance is '
        f'{vd_stress.diversification_share * 100:+.0f}% of portfolio variance.</div>',
        unsafe_allow_html=True)

# --- Deterministic interpretation --------------------------------------------
section("Portfolio interpretation")
paras = []
pc1_d = pc1_stress - pc1_calm
neff_d = neff_stress - neff_calm
corr_d = avg_stress - avg_calm
if pc1_d > 0.02 and neff_d < 0:
    paras.append(f"The selected portfolio becomes <b>more concentrated in stress</b>: PC1 share rises "
                 f"{pc1_calm * 100:.0f}% → {pc1_stress * 100:.0f}% and effective bets fall "
                 f"{neff_calm:.2f} → {neff_stress:.2f}, so a larger share of variation loads on one common "
                 f"direction and fewer independent bets remain.")
elif pc1_d <= 0.02 and neff_d >= 0:
    paras.append(f"The selected portfolio does <b>not</b> concentrate materially in stress (PC1 "
                 f"{pc1_calm * 100:.0f}% → {pc1_stress * 100:.0f}%, effective bets {neff_calm:.2f} → {neff_stress:.2f}).")
else:
    paras.append(f"Concentration signals are mixed (PC1 {pc1_calm * 100:.0f}% → {pc1_stress * 100:.0f}%, "
                 f"effective bets {neff_calm:.2f} → {neff_stress:.2f}).")
if corr_d >= 0.05:
    paras.append(f"Average pairwise correlation rises substantially ({avg_calm:+.2f} → {avg_stress:+.2f}): "
                 f"co-movement increases broadly across the selected assets in stress.")
elif abs(corr_d) < 0.05 and pc1_d > 0.02:
    paras.append(f"Average correlation is nearly flat ({avg_calm:+.2f} → {avg_stress:+.2f}) yet PC1 rises — a "
                 f"structural reshuffle: the mean masks concentration at the system level.")
else:
    paras.append(f"Average pairwise correlation moves {avg_calm:+.2f} → {avg_stress:+.2f} between regimes.")
# hedge assets present?
hedge_assets = [a for a in selected if ASSET_ROLE.get(a) in {"treasury", "gold"}]
if hedge_assets:
    hedge_stress_contrib = {a: rc_stress.percent[selected.index(a)] for a in hedge_assets}
    lowest = min(hedge_stress_contrib, key=hedge_stress_contrib.get)
    share = hedge_stress_contrib[lowest] * 100
    share_txt = ("a near-zero" if abs(share) < 0.5 else
                 f"a negative ({share:.0f}%)" if share < 0 else f"only a {share:.0f}%")
    paras.append(f"Potential diversifiers in the mix ({', '.join(hedge_assets)}) carry a relatively small share of "
                 f"stress risk — {lowest} contributes {share_txt} share of stress volatility, "
                 f"consistent with its low or negative stress correlations.")
paras.append(f"Portfolio volatility scales by <b>{mult:.2f}×</b> from calm to stress. This is a descriptive "
             f"regime diagnostic on historical data — not an optimization, forecast, or investment recommendation.")
interpretation_panel(paras, title="Diagnostic reading")
