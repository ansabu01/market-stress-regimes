"""
Publication figures for the Markov-switching SPY regimes.

Reproduces the multi-panel ``Regimes.png`` aesthetic (price panel + stress-
probability panel + regime swim-lanes) for the monthly and weekly Markov
regimes, and visualises how much they agree with each other and with the
rule-based VIX + drawdown labels.

Reads the DuckDB tables built by scripts 04 / 05.00 / 05.01 and writes PNGs to
``outputs/02_regimes/``. Orchestrated by ``notebooks/02_markov_regime.ipynb``.


NOTE: THIS IS AN AI generated script. I did not write the lines but asserted the correctness

.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec

from regimes.markov_switching import MONTHLY, WEEKLY, RegimeConfig

# --- Aesthetic (matches the regime notebook's Regimes.png cell) --------------
C_PRICE = "#7aadcc"
C_PROB = "#b22222"
C_THR = "#d4781a"
C_BAND = "#fccaca"
LANE_PRIMARY = "#b22222"
LANE_RULE = "#1565c0"
LANE_OTHER = "#e07b39"

EVENTS = [
    ("2001-09-17", "9/11"),
    ("2002-10-09", "Dot-com"),
    ("2008-10-27", "GFC"),
    ("2011-08-08", "EU debt"),
    ("2018-12-24", "Q4 2018"),
    ("2020-03-20", "COVID-19"),
    ("2022-10-13", "Rate hikes"),
]

FREQ_LABEL = {"M": "Monthly", "W": "Weekly"}


def stress_segments(dates: pd.Series, flag) -> list[tuple]:
    """Collapse a boolean stress flag into (start, end) date segments."""
    flag = np.asarray(flag, dtype=bool)
    dates = pd.Series(pd.to_datetime(dates)).reset_index(drop=True)
    segs, in_s, t0 = [], False, None
    for dt, f in zip(dates, flag):
        if f and not in_s:
            t0, in_s = dt, True
        elif not f and in_s:
            segs.append((t0, dt))
            in_s = False
    if in_s and t0 is not None:
        segs.append((t0, dates.iloc[-1]))
    return segs


def _shade(ax, segs, color=C_BAND, alpha=0.42, zorder=0) -> None:
    for t0, t1 in segs:
        ax.axvspan(t0, t1, color=color, alpha=alpha, lw=0, zorder=zorder)


def _broadcast_to_daily(
    daily_dates: pd.Series,
    period_df: pd.DataFrame,
    period_col: str,
    value_col: str,
    pandas_freq: str,
    fill,
) -> np.ndarray:
    """Map a per-period column onto a daily date grid via the calendar period."""
    pf = period_df.copy()
    pf["__pk"] = pd.to_datetime(pf[period_col]).dt.to_period(pandas_freq)
    lookup = dict(zip(pf["__pk"], pf[value_col]))
    keys = pd.PeriodIndex(pd.to_datetime(daily_dates), freq=pandas_freq)
    return np.array([lookup.get(k, fill) for k in keys])


def plot_markov_regime(
    con: duckdb.DuckDBPyConnection,
    primary: RegimeConfig,
    other: RegimeConfig,
    out_path: Path,
) -> Path:
    """Render one Regimes.png-style figure for ``primary`` with an agreement panel."""
    primary_name = FREQ_LABEL.get(primary.model_frequency, primary.model_frequency)
    other_name = FREQ_LABEL.get(other.model_frequency, other.model_frequency)

    # --- Load data ----------------------------------------------------------
    spy = con.execute(
        """
        SELECT date, price AS adj_close
        FROM asset_prices
        WHERE ticker = 'SPY' AND price_source = 'adj_close'
        ORDER BY date
        """
    ).fetchdf()
    spy["date"] = pd.to_datetime(spy["date"])

    prim = con.execute(
        f"SELECT {primary.period_column}, ms_prob_stress, ms_stress_50 "
        f"FROM {primary.regime_table} ORDER BY {primary.period_column}"
    ).fetchdf()
    oth = con.execute(
        f"SELECT {other.period_column}, ms_stress_50 "
        f"FROM {other.regime_table} ORDER BY {other.period_column}"
    ).fetchdf()

    # --- Daily-aligned series -----------------------------------------------
    dates = spy["date"]
    prim_stress = _broadcast_to_daily(
        dates, prim, primary.period_column, "ms_stress_50", primary.pandas_freq, fill=0
    ).astype(bool)
    prim_prob = _broadcast_to_daily(
        dates, prim, primary.period_column, "ms_prob_stress", primary.pandas_freq,
        fill=np.nan,
    ).astype(float)
    other_stress = _broadcast_to_daily(
        dates, oth, other.period_column, "ms_stress_50", other.pandas_freq, fill=0
    ).astype(bool)

    rule = con.execute(
        "SELECT date, stress_raw FROM regime_labels ORDER BY date"
    ).fetchdf()
    rule["date"] = pd.to_datetime(rule["date"])
    rule_daily = (
        spy[["date"]]
        .merge(rule, on="date", how="left")["stress_raw"]
        .fillna(0)
        .astype(bool)
        .to_numpy()
    )

    segs_primary = stress_segments(dates, prim_stress)
    segs_other = stress_segments(dates, other_stress)
    segs_rule = stress_segments(dates, rule_daily)

    prim_share = float(prim_stress.mean())

    # --- Figure -------------------------------------------------------------
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(3, 1, figure=fig, height_ratios=[4, 3, 2.4], hspace=0.07)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax3 = fig.add_subplot(gs[2], sharex=ax1)

    # Panel 1: SPY price (log) with stress bands
    _shade(ax1, segs_primary)
    ax1.plot(dates, spy["adj_close"], color=C_PRICE, lw=1.0, label="SPY adj. close")
    ax1.set_yscale("log")
    ax1.set_ylabel("SPY (log scale)", fontsize=10)
    xf = ax1.get_xaxis_transform()
    for dt_str, lbl in EVENTS:
        dt = pd.Timestamp(dt_str)
        if dates.min() <= dt <= dates.max():
            ax1.axvline(dt, color="#cccccc", lw=0.9, ls=":", zorder=1)
            ax1.text(
                dt, 0.97, lbl, fontsize=6.5, color="#555", ha="center", va="top",
                transform=xf,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.80),
            )
    stress_patch = mpatches.Patch(facecolor=C_BAND, alpha=0.7,
                                  label=f"{primary_name} Markov stress")
    h, l = ax1.get_legend_handles_labels()
    ax1.legend(h + [stress_patch], l + [f"{primary_name} Markov stress"],
               loc="upper left", fontsize=8.5, framealpha=0.92)
    ax1.set_title(
        f"{primary_name} Markov-switching SPY regime  ·  two-state, switching "
        f"mean and variance  ·  stress = high-variance state  ({prim_share:.0%} of days)",
        fontsize=12, fontweight="bold", pad=10,
    )
    ax1.grid(axis="y", color="#ebebeb", lw=0.7)
    ax1.tick_params(labelbottom=False)

    # Panel 2: smoothed stress probability
    _shade(ax2, segs_primary)
    ax2.fill_between(dates, prim_prob, color=C_PROB, alpha=0.18, lw=0)
    ax2.plot(dates, prim_prob, color=C_PROB, lw=1.0,
             label="Smoothed P(stress)")
    ax2.axhline(0.5, color=C_THR, lw=1.2, ls="--", alpha=0.9, label="0.5 threshold (primary)")
    ax2.axhline(0.75, color="#999999", lw=1.0, ls=":", alpha=0.9, label="0.75 threshold")
    ax2.set_ylim(-0.03, 1.03)
    ax2.set_ylabel("P(stress)", fontsize=10)
    ax2.legend(loc="upper left", fontsize=8.0, framealpha=0.92, ncol=3)
    ax2.grid(axis="y", color="#ebebeb", lw=0.7)
    ax2.tick_params(labelbottom=False)

    # Panel 3: regime swim-lanes (agreement at a glance)
    lanes = [
        (segs_primary, f"{primary_name} Markov (P≥0.5)", LANE_PRIMARY),
        (segs_rule, "Rule-based (VIX q75 + 5% drawdown)", LANE_RULE),
        (segs_other, f"{other_name} Markov (P≥0.5)", LANE_OTHER),
    ]
    gap, n = 0.16, len(lanes)
    for row, (segs, label, color) in enumerate(lanes):
        y0 = (n - 1 - row) * (1 + gap)
        y1 = y0 + 1.0
        ax3.fill_between([dates.iloc[0], dates.iloc[-1]], y0, y1, color="#f4f4f4",
                         lw=0, zorder=0)
        for t0, t1 in segs:
            ax3.fill_between([t0, t1], y0, y1, color=color, alpha=0.82, lw=0, zorder=1)
        ax3.text(dates.iloc[5], (y0 + y1) / 2, label, fontsize=8.0, va="center",
                 color=color, fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none", alpha=0.88))
    ax3.set_ylim(-0.08, n * (1 + gap))
    ax3.set_yticks([])
    ax3.set_ylabel("Stress\ndefinitions", fontsize=9, labelpad=2)
    ax3.set_xlabel("Date", fontsize=10)
    ax3.grid(axis="x", color="#ebebeb", lw=0.7)

    # Shared x-axis formatting
    ax3.xaxis.set_major_locator(mdates.YearLocator(2))
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax3.xaxis.set_minor_locator(mdates.YearLocator(1))
    plt.setp(ax3.xaxis.get_majorticklabels(), fontsize=9.5)
    for ax in (ax1, ax2, ax3):
        ax.set_xlim(dates.min(), dates.max())
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines["left"].set_color("#d0d0d0")
        ax.spines["bottom"].set_color("#d0d0d0")
        ax.tick_params(colors="#444444")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


def generate_regime_figures(con: duckdb.DuckDBPyConnection, out_dir: Path) -> list[Path]:
    """Render both the monthly and weekly Markov regime figures."""
    return [
        plot_markov_regime(con, MONTHLY, WEEKLY, out_dir / "markov_regime_monthly.png"),
        plot_markov_regime(con, WEEKLY, MONTHLY, out_dir / "markov_regime_weekly.png"),
    ]
