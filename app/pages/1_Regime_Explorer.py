"""Regime Explorer — when was the market stressed, and how sensitive is the label?"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402
from pandas.api.types import is_bool_dtype, is_numeric_dtype  # noqa: E402

from app.utils.components import caption, interpretation_panel, page_header, section, stat_card, stat_row  # noqa: E402
from app.utils.data import load_parquet  # noqa: E402
from app.utils.plotting import FONT_FAMILY, base_layout, style_axes  # noqa: E402
from app.utils.theme import PALETTE, SEMANTIC, configure_page  # noqa: E402

configure_page("Regime Explorer")

OFFICIAL = SEMANTIC["calm"]
STRESS = SEMANTIC["stress"]
SELECTED = SEMANTIC["vol_sensitive"]
STRICT = PALETTE["text_faint"]
WEEKLY = SEMANTIC["mostly_resilient"]
RULE = SEMANTIC["resilient"]


@dataclass(frozen=True)
class Lane:
    label: str
    column: str
    color: str
    group: str


def _as_bool(series: pd.Series) -> pd.Series:
    if series.empty:
        return pd.Series(dtype=bool)
    if is_bool_dtype(series):
        return series.fillna(False).astype(bool)
    if is_numeric_dtype(series):
        return series.fillna(0).astype(float) > 0
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().any():
        return numeric.fillna(0).astype(float) > 0
    return series.fillna("").astype(str).str.strip().str.lower().isin(
        {"1", "true", "t", "yes", "y", "stress", "stressed"})


@st.cache_data(show_spinner=False)
def load_regime() -> pd.DataFrame:
    frame = load_parquet("regime_timeseries.parquet")
    if frame.empty:
        return frame
    frame = frame.copy()
    for col in ["date", "markov_month_end", "markov_week_end"]:
        if col in frame.columns:
            frame[col] = pd.to_datetime(frame[col])
    for col in ["spy_adj_close", "ms_prob_stress_monthly", "ms_prob_stress_weekly", "spx_drawdown"]:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame.sort_values("date").reset_index(drop=True)


def stress_runs(frame: pd.DataFrame, column: str) -> list[dict]:
    if frame.empty or column not in frame.columns:
        return []
    clean = frame[["date", column]].reset_index(drop=True)
    flags = _as_bool(clean[column]).to_numpy()
    runs, start = [], None
    for pos, flag in enumerate(flags):
        if flag and start is None:
            start = pos
        elif not flag and start is not None:
            runs.append({"start": clean.loc[start, "date"], "end": clean.loc[pos - 1, "date"],
                         "start_pos": start, "end_pos": pos - 1, "days": pos - start})
            start = None
    if start is not None:
        runs.append({"start": clean.loc[start, "date"], "end": clean.loc[len(clean) - 1, "date"],
                     "start_pos": start, "end_pos": len(clean) - 1, "days": len(clean) - start})
    return runs


def episode_table(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    rows = []
    for run in stress_runs(frame, column):
        seg = frame.iloc[run["start_pos"]:run["end_pos"] + 1]
        prob = pd.to_numeric(seg.get("ms_prob_stress_monthly"), errors="coerce")
        prices = pd.to_numeric(seg.get("spy_adj_close"), errors="coerce").dropna()
        spy_ret = (prices.iloc[-1] / prices.iloc[0] - 1) if len(prices) >= 2 and prices.iloc[0] > 0 else None
        rows.append({
            "start": run["start"], "end": run["end"], "trading_days": run["days"],
            "mean_p": float(prob.mean()) if prob.notna().any() else None,
            "max_p": float(prob.max()) if prob.notna().any() else None,
            "spy_return": spy_ret,
        })
    return pd.DataFrame(rows).sort_values("start", ascending=False).reset_index(drop=True) if rows else pd.DataFrame()


def metrics(frame: pd.DataFrame, column: str) -> dict:
    flags = _as_bool(frame[column]) if column in frame.columns else pd.Series(dtype=bool)
    eps = episode_table(frame, column)
    days = int(flags.sum())
    obs = max(int(flags.notna().sum()), 1)
    return {"episodes": len(eps), "days": days, "share": days / obs,
            "avg_dur": float(eps["trading_days"].mean()) if not eps.empty else 0.0}


regime = load_regime()
if regime.empty or not {"date", "spy_adj_close", "ms_prob_stress_monthly"}.issubset(regime.columns):
    page_header("Regime identification", "Regime Explorer",
                "Regime timeline data is unavailable — export dashboard data first.")
    st.stop()

page_header(
    "Regime identification · Result validation",
    "When was the market classified as stressed?",
    "The official monthly Markov 0.50 label is fixed. The threshold slider recomputes a descriptive "
    "exploratory label from stored P(stress) — it does not refit the Markov model.",
    provenance="official",
)

min_date = pd.Timestamp(regime["date"].min()).to_pydatetime()
max_date = pd.Timestamp(regime["date"].max()).to_pydatetime()
with st.sidebar:
    st.header("Controls")
    threshold = st.slider("Exploratory P(stress) threshold", 0.05, 0.95, 0.50, 0.01,
                          help="Derives a descriptive label from stored monthly P(stress). The official label stays at 0.50.")
    window = st.slider("Analysis window", min_value=min_date, max_value=max_date,
                       value=(min_date, max_date), format="YYYY-MM-DD")
    show_weekly = st.checkbox("Overlay weekly P(stress)", value=True,
                              disabled="ms_prob_stress_weekly" not in regime.columns)

start, end = pd.to_datetime(window[0]), pd.to_datetime(window[1])
view = regime[(regime["date"] >= start) & (regime["date"] <= end)].copy()
if view.empty:
    st.warning("The selected window contains no observations.")
    st.stop()

view["selected_stress"] = view["ms_prob_stress_monthly"].fillna(-1).astype(float) >= threshold
if "ms_stress_50_monthly" in view.columns:
    view["official_stress"] = _as_bool(view["ms_stress_50_monthly"])
else:
    view["official_stress"] = view["ms_prob_stress_monthly"].fillna(-1).astype(float) >= 0.50
if "ms_stress_75_monthly" in view.columns:
    view["strict_stress"] = _as_bool(view["ms_stress_75_monthly"])
else:
    view["strict_stress"] = view["ms_prob_stress_monthly"].fillna(-1).astype(float) >= 0.75
if "ms_stress_50_weekly" in view.columns:
    view["weekly_stress"] = _as_bool(view["ms_stress_50_weekly"])
for col in ["stress_raw", "stress_smooth_21d"]:
    if col in view.columns:
        view[col] = _as_bool(view[col])

sel, off = metrics(view, "selected_stress"), metrics(view, "official_stress")

d_days, c_days = (SEMANTIC["stress"] if sel["days"] > off["days"] else SEMANTIC["calm"]), None
stat_row([
    stat_card("Official stress-day share", f"{off['share'] * 100:.1f}%", sub="Monthly Markov 0.50 (fixed)"),
    stat_card("Selected-threshold share", f"{sel['share'] * 100:.1f}%",
              delta=f"{(sel['share'] - off['share']) * 100:+.1f} pp vs 0.50",
              delta_color=(SEMANTIC["stress"] if sel["share"] > off["share"] else SEMANTIC["calm"]),
              sub=f"Exploratory label at {threshold:.2f}"),
    stat_card("Detected episodes", f"{sel['episodes']}",
              delta=f"{sel['episodes'] - off['episodes']:+d} vs 0.50", sub="Contiguous stress spans"),
    stat_card("Avg episode length", f"{sel['avg_dur']:.0f} days",
              sub="Trading days per selected-threshold episode"),
])

# --- Main timeline figure -----------------------------------------------------
section("SPY, stress probability, and label agreement")
lanes = [Lane("Monthly Markov 0.50", "official_stress", OFFICIAL, "Official"),
         Lane(f"Selected {threshold:.2f}", "selected_stress", SELECTED, "Exploratory"),
         Lane("Monthly Markov 0.75", "strict_stress", STRICT, "Exploratory")]
for lane in [Lane("Weekly Markov 0.50", "weekly_stress", WEEKLY, "Robustness"),
             Lane("Rule: VIX + drawdown", "stress_raw", RULE, "Rule-based"),
             Lane("Rule: smoothed 21d", "stress_smooth_21d", SEMANTIC["neutral"], "Rule-based")]:
    if lane.column in view.columns:
        lanes.append(lane)

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.045,
                    row_heights=[0.44, 0.30, 0.26], specs=[[{"secondary_y": True}], [{}], [{}]])
for run in stress_runs(view, "selected_stress"):
    for r in (1, 2):
        fig.add_vrect(x0=run["start"], x1=run["end"] + pd.Timedelta(days=1),
                      fillcolor=SELECTED, opacity=0.12, line_width=0, layer="below", row=r, col=1)

fig.add_trace(go.Scatter(x=view["date"], y=view["spy_adj_close"], mode="lines",
                         line=dict(color=PALETTE["text"], width=1.3), name="SPY",
                         hovertemplate="%{x|%Y-%m-%d}<br>SPY: %{y:.2f}<extra></extra>"),
              row=1, col=1, secondary_y=False)
if "spx_drawdown" in view.columns and view["spx_drawdown"].notna().any():
    fig.add_trace(go.Scatter(x=view["date"], y=view["spx_drawdown"], mode="lines",
                             line=dict(color=SEMANTIC["neutral"], width=0.8), name="Drawdown", opacity=0.7,
                             hovertemplate="%{x|%Y-%m-%d}<br>Drawdown: %{y:.1%}<extra></extra>"),
                  row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Drawdown", range=[-0.65, 0.05], tickformat=".0%", showgrid=False,
                     row=1, col=1, secondary_y=True)

fig.add_trace(go.Scatter(x=view["date"], y=view["ms_prob_stress_monthly"], mode="lines", fill="tozeroy",
                         line=dict(color=STRESS, width=1.7), fillcolor="rgba(240,136,62,0.12)",
                         name="Monthly P(stress)",
                         hovertemplate="%{x|%Y-%m-%d}<br>P(stress): %{y:.3f}<extra></extra>"), row=2, col=1)
if show_weekly and "ms_prob_stress_weekly" in view.columns:
    fig.add_trace(go.Scatter(x=view["date"], y=view["ms_prob_stress_weekly"], mode="lines",
                             line=dict(color=WEEKLY, width=0.9, dash="dot"), opacity=0.8, name="Weekly P(stress)",
                             hovertemplate="%{x|%Y-%m-%d}<br>Weekly P(stress): %{y:.3f}<extra></extra>"), row=2, col=1)
for value, color, dash, label in [(threshold, SELECTED, "dash", f"Selected {threshold:.2f}"),
                                  (0.50, OFFICIAL, "solid", "Official 0.50"), (0.75, STRICT, "dot", "0.75")]:
    fig.add_hline(y=value, line_color=color, line_dash=dash, line_width=1.1,
                  annotation_text=label, annotation_position="top left",
                  annotation_font=dict(size=9, color=color), row=2, col=1)

y_positions = list(range(len(lanes), 0, -1))
for lane, y in zip(lanes, y_positions):
    fig.add_trace(go.Scatter(x=[view["date"].min(), view["date"].max()], y=[y, y], mode="lines",
                             line=dict(color=PALETTE["panel"], width=16), hoverinfo="skip", showlegend=False),
                  row=3, col=1)
    xs, ys, cd = [], [], []
    for run in stress_runs(view, lane.column):
        xs += [run["start"], run["end"] + pd.Timedelta(days=1), None]
        ys += [y, y, None]
        info = (run["start"].strftime("%Y-%m-%d"), run["end"].strftime("%Y-%m-%d"), run["days"], lane.group)
        cd += [info, info, None]
    if xs:
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=lane.color, width=14),
                                 name=lane.label, customdata=cd, showlegend=False,
                                 hovertemplate=f"<b>{lane.label}</b> · %{{customdata[3]}}<br>"
                                 "%{customdata[0]} → %{customdata[1]}<br>%{customdata[2]} trading days<extra></extra>"),
                      row=3, col=1)
fig.update_yaxes(tickmode="array", tickvals=y_positions, ticktext=[l.label for l in lanes],
                 range=[0.4, len(lanes) + 0.6], row=3, col=1, tickfont=dict(size=10))
fig.update_yaxes(title_text="SPY (log)", type="log", row=1, col=1, secondary_y=False)
fig.update_yaxes(title_text="P(stress)", range=[-0.04, 1.04], tickformat=".0%", row=2, col=1)
fig.update_layout(**base_layout(760, legend=True, hovermode="x unified", margin=dict(l=48, r=48, t=30, b=36)))
style_axes(fig)
st.plotly_chart(fig, width="stretch")
caption(f"Shaded spans = selected exploratory threshold ({threshold:.2f}). Official 0.50 and weekly/rule labels are shown for comparison, unchanged.")

# --- Episodes + interpretation ------------------------------------------------
left, right = st.columns([1.3, 1])
with left:
    section("Detected stress episodes (selected threshold)")
    eps = episode_table(view, "selected_stress")
    if eps.empty:
        st.info("No stress episodes at the selected threshold and window.")
    else:
        disp = eps.copy()
        disp["start"] = disp["start"].dt.strftime("%Y-%m-%d")
        disp["end"] = disp["end"].dt.strftime("%Y-%m-%d")
        disp["spy_return"] = disp["spy_return"] * 100
        st.dataframe(disp, hide_index=True, width="stretch", column_config={
            "start": st.column_config.TextColumn("Start"), "end": st.column_config.TextColumn("End"),
            "trading_days": st.column_config.NumberColumn("Trading days", format="%d"),
            "mean_p": st.column_config.NumberColumn("Mean P(stress)", format="%.2f"),
            "max_p": st.column_config.NumberColumn("Peak P(stress)", format="%.2f"),
            "spy_return": st.column_config.NumberColumn("SPY return", format="%.1f%%")})

with right:
    section("Reading the timeline")
    strict = metrics(view, "strict_stress")
    move = "raises" if sel["share"] > off["share"] else ("lowers" if sel["share"] < off["share"] else "matches")
    interpretation_panel([
        f"At the <b>0.50</b> maximum-probability rule the official label marks "
        f"<b>{off['share'] * 100:.0f}%</b> of days as stress across <b>{off['episodes']}</b> episodes in this window.",
        f"Moving the exploratory threshold to <b>{threshold:.2f}</b> {move} the stress share to "
        f"<b>{sel['share'] * 100:.0f}%</b>, and the stricter <b>0.75</b> cut-off isolates only "
        f"<b>{strict['share'] * 100:.0f}%</b> — high-confidence stress.",
        "The regimes are persistent (multi-month spells), so this is a high-volatility <b>era</b> label, "
        "not a crash-day flag. Threshold changes only re-shade a fixed probability path.",
    ])

with st.expander("Markov transition matrix (official)", expanded=False):
    tm = load_parquet("markov_chain_transition_matrix.parquet")
    if tm.empty:
        st.info("Transition matrix export not available.")
    else:
        st.dataframe(tm, hide_index=True, width="stretch")
        caption("Fixed after fitting: only the state probabilities vary over time, not the transition matrix.")
