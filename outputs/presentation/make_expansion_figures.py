"""Generate the story-expansion figures for the seminar deck.

All figures are computed from the project's canonical data (DuckDB pipeline
tables / measured report quantities) — nothing is invented. Style matches the
existing deck: calm #4C78A8, stress #B22222, dark ink #22262E, white background.

Outputs -> outputs/presentation/figures/
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FIG_DIR = HERE / "figures"
FIG_DIR.mkdir(exist_ok=True)
DB = HERE.parents[1] / "data" / "lsr.duckdb"

NAVY = "#22262E"
CALM = "#4C78A8"
STRESS = "#B22222"
GOLD = "#B8860B"
GREY = "#8a94a3"
GRID = "#e6eaf0"

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": "#c9cfd8", "axes.linewidth": 0.8,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "font.size": 11, "axes.titlesize": 12.5, "axes.titleweight": "bold",
    "axes.titlecolor": NAVY, "axes.labelcolor": "#4a5261",
    "xtick.color": "#4a5261", "ytick.color": "#4a5261",
    "axes.spines.top": False, "axes.spines.right": False,
})


def save(fig, name):
    fig.savefig(FIG_DIR / name, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[ok] {name}")


# ---------------------------------------------------------------------------
# 1. The free lunch and its floor: sigma_p/sigma vs N for measured avg corr
#    (equal-weight formula from the report appendix; rho-bar from the pipeline)
# ---------------------------------------------------------------------------

def fig_free_lunch(avg_corrs: dict[str, float]):
    n = np.arange(1, 31)

    def rel_vol(rho):
        return np.sqrt(1.0 / n + (1.0 - 1.0 / n) * rho)

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.plot(n, rel_vol(0.0), color=GREY, ls="--", lw=1.6,
            label="Uncorrelated ideal  (ρ̄ = 0)")
    series = [
        ("Cross-asset, calm  (ρ̄ = %.2f)" % avg_corrs["panel_a_calm"], avg_corrs["panel_a_calm"], CALM, "-"),
        ("International equity, calm  (ρ̄ = %.2f)" % avg_corrs["panel_b_calm"], avg_corrs["panel_b_calm"], "#d98b6a", "-"),
        ("International equity, stress  (ρ̄ = %.2f)" % avg_corrs["panel_b_stress"], avg_corrs["panel_b_stress"], STRESS, "-"),
    ]
    for label, rho, color, ls in series:
        ax.plot(n, rel_vol(rho), color=color, lw=2.4, ls=ls, label=label)
        ax.axhline(np.sqrt(rho), color=color, lw=0.9, ls=":", alpha=0.7)
        ax.annotate(f"floor √ρ̄ = {np.sqrt(rho):.2f}", xy=(30, np.sqrt(rho)),
                    xytext=(30.4, np.sqrt(rho)), fontsize=9.5, color=color,
                    va="center", annotation_clip=False)

    ax.set_xlim(1, 30)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Number of equally weighted assets  N")
    ax.set_ylabel("Portfolio volatility  ÷  single-asset volatility")
    ax.set_title("Adding assets removes idiosyncratic risk — average correlation sets the floor")
    ax.legend(frameon=False, loc="upper right", fontsize=9.5)
    fig.tight_layout()
    save(fig, "fig_free_lunch.png")


# ---------------------------------------------------------------------------
# 2. 2008 vs 2022: growth of 100 for SPY / TLT / GLD in the two stress windows
# ---------------------------------------------------------------------------

def fig_hedges_2008_2022(con):
    prices = con.execute("""
        SELECT date, ticker, price FROM asset_prices
        WHERE ticker IN ('SPY','TLT','GLD') AND price_source='adj_close'
        ORDER BY date
    """).fetchdf()
    prices["date"] = pd.to_datetime(prices["date"])
    wide = prices.pivot(index="date", columns="ticker", values="price").dropna()

    windows = [
        ("Global financial crisis", "2007-10-01", "2009-06-30"),
        ("Inflation & rate shock", "2022-01-01", "2023-10-31"),
    ]
    colors = {"SPY": NAVY, "TLT": CALM, "GLD": GOLD}
    stats = {}

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.3), sharey=True)
    for ax, (title, start, end) in zip(axes, windows):
        window = wide.loc[start:end]
        indexed = window / window.iloc[0] * 100.0
        for ticker in ["SPY", "TLT", "GLD"]:
            ax.plot(indexed.index, indexed[ticker], color=colors[ticker], lw=2.0, label=ticker)
            final = indexed[ticker].iloc[-1]
            low = indexed[ticker].min()
            stats[(title, ticker)] = (low, final)
            ax.annotate(f"{ticker}  {final - 100:+.0f}%", xy=(indexed.index[-1], final),
                        xytext=(6, 0), textcoords="offset points", fontsize=10,
                        color=colors[ticker], fontweight="bold", va="center")
        ax.axhline(100, color="#9aa3af", lw=0.9, ls="--")
        ax.set_title(f"{title}  ({start[:4]}–{end[:4]})")
        ax.set_xlim(indexed.index[0], indexed.index[-1] + pd.Timedelta(days=170))
        ax.tick_params(axis="x", labelsize=9)
    axes[0].set_ylabel("Growth of 100 (window start = 100)")
    fig.tight_layout()
    save(fig, "fig_hedges_2008_2022.png")
    return stats


# ---------------------------------------------------------------------------
# 3. Forbes-Rigobon mechanism: measured corr vs variance ratio (paper Eq.)
# ---------------------------------------------------------------------------

def fig_fr_mechanism(spy_ratio: float):
    ratio = np.linspace(1.0, 8.0, 300)
    delta = ratio - 1.0

    def measured(rho):
        return rho * np.sqrt(1.0 + delta) / np.sqrt(1.0 + delta * rho**2)

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    shades = ["#8fb3d9", CALM, "#2c4f7c"]
    for rho, color in zip([0.3, 0.5, 0.7], shades):
        ax.plot(ratio, measured(rho), color=color, lw=2.4, label=f"true ρ = {rho:.1f}")
        # marker at SPY's measured shock
        d = spy_ratio - 1.0
        m = rho * np.sqrt(1.0 + d) / np.sqrt(1.0 + d * rho**2)
        ax.plot([spy_ratio], [m], "o", color=color, ms=7, zorder=5)
        ax.annotate(f"{m:.2f}", xy=(spy_ratio, m), xytext=(8, -2), textcoords="offset points",
                    fontsize=9.5, color=color, fontweight="bold")
    ax.axvline(spy_ratio, color=STRESS, lw=1.4, ls="--")
    ax.annotate(f"SPY in stress:\nvariance × {spy_ratio:.2f}  (δ = {spy_ratio - 1:.2f})",
                xy=(spy_ratio, 0.14), xytext=(spy_ratio + 0.25, 0.08),
                fontsize=10, color=STRESS, fontweight="bold")
    ax.set_xlim(1, 8)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("Stress-to-calm variance ratio of the market factor")
    ax.set_ylabel("Measured stress correlation")
    ax.set_title("An unchanged relationship still shows a higher correlation\nwhen the common factor gets more volatile")
    ax.legend(frameon=False, loc="lower right", fontsize=10)
    fig.tight_layout()
    save(fig, "fig_fr_mechanism.png")


# ---------------------------------------------------------------------------
# 4. PCA spectrum: Panel A eigenvalue shares, calm vs stress (pipeline table)
# ---------------------------------------------------------------------------

def fig_pca_spectrum(con):
    eig = con.execute("""
        SELECT regime, component, explained_variance_share
        FROM pca_regime_concentration_eigenvalues
        WHERE universe='panel_a_cross_asset' AND regime IN ('calm','stress')
        ORDER BY regime, component
    """).fetchdf()
    calm = eig[eig.regime == "calm"].set_index("component")["explained_variance_share"]
    stress = eig[eig.regime == "stress"].set_index("component")["explained_variance_share"]
    comps = calm.index.to_numpy()

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    width = 0.38
    ax.bar(comps - width / 2, calm.values, width, color=CALM, label="Calm")
    ax.bar(comps + width / 2, stress.values, width, color=STRESS, label="Stress")
    for c in (1, 2):
        for series, offset, color in [(calm, -width / 2, CALM), (stress, width / 2, STRESS)]:
            ax.annotate(f"{series[c] * 100:.1f}%", xy=(c + offset, series[c]),
                        xytext=(0, 4), textcoords="offset points", ha="center",
                        fontsize=10, fontweight="bold", color=color)
    ax.annotate("", xy=(1.32, stress[1] - 0.012), xytext=(2.30, stress[2] + 0.012),
                arrowprops=dict(arrowstyle="->", color=NAVY, lw=1.6,
                                connectionstyle="arc3,rad=-0.35"))
    ax.text(1.86, 0.395, "variance migrates\nPC2 → PC1", ha="center", fontsize=10,
            color=NAVY, fontweight="bold")
    ax.set_xticks(comps)
    ax.set_xlabel("Principal component")
    ax.set_ylabel("Share of total variance")
    ax.set_ylim(0, 0.46)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v * 100:.0f}%")
    ax.set_title("Cross-asset panel: stress feeds the second axis into the first")
    ax.legend(frameon=False, fontsize=10)
    fig.tight_layout()
    save(fig, "fig_pca_spectrum.png")


# ---------------------------------------------------------------------------
# 5. Dark SPY sparkline strip with stress shading (title slide footer)
# ---------------------------------------------------------------------------

def fig_title_strip(con):
    spy = con.execute("""
        SELECT date, price FROM asset_prices
        WHERE ticker='SPY' AND price_source='adj_close' ORDER BY date
    """).fetchdf()
    spy["date"] = pd.to_datetime(spy["date"])
    monthly = con.execute("""
        SELECT month_end, ms_stress_50 FROM markov_regime_monthly ORDER BY month_end
    """).fetchdf()
    monthly["month"] = pd.to_datetime(monthly["month_end"]).dt.to_period("M")
    spy["month"] = spy["date"].dt.to_period("M")
    spy = spy.merge(monthly[["month", "ms_stress_50"]], on="month", how="left")
    spy["stress"] = spy["ms_stress_50"].fillna(False).astype(bool)

    fig, ax = plt.subplots(figsize=(13.4, 0.85))
    fig.patch.set_facecolor(NAVY)
    ax.set_facecolor(NAVY)
    # stress spans
    in_span, start = False, None
    for i in range(len(spy)):
        s = bool(spy["stress"].iloc[i])
        if s and not in_span:
            start, in_span = spy["date"].iloc[i], True
        elif not s and in_span:
            ax.axvspan(start, spy["date"].iloc[i - 1], color=STRESS, alpha=0.30, lw=0)
            in_span = False
    if in_span:
        ax.axvspan(start, spy["date"].iloc[-1], color=STRESS, alpha=0.30, lw=0)
    ax.plot(spy["date"], np.log(spy["price"]), color="#CADCFC", lw=1.0)
    ax.set_xlim(spy["date"].min(), spy["date"].max())
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(FIG_DIR / "fig_title_strip.png", dpi=200, facecolor=NAVY)
    plt.close(fig)
    print("[ok] fig_title_strip.png")


def main():
    con = duckdb.connect(str(DB), read_only=True)
    corr = con.execute("""
        SELECT universe, regime, AVG(correlation) AS avg_corr FROM correlation_pairs
        WHERE regime IN ('calm','stress') GROUP BY universe, regime
    """).fetchdf().set_index(["universe", "regime"])["avg_corr"]
    avg_corrs = {
        "panel_a_calm": float(corr[("panel_a_cross_asset", "calm")]),
        "panel_b_calm": float(corr[("panel_b_international_equity", "calm")]),
        "panel_b_stress": float(corr[("panel_b_international_equity", "stress")]),
    }
    print("avg corrs:", {k: round(v, 3) for k, v in avg_corrs.items()})
    spy_ratio = float(con.execute("""
        SELECT variance_ratio FROM forbes_rigobon_variance_ratios
        WHERE universe='etf_assets' AND asset='SPY'
    """).fetchone()[0])
    print("SPY variance ratio:", round(spy_ratio, 3))

    fig_free_lunch(avg_corrs)
    stats = fig_hedges_2008_2022(con)
    for k, v in stats.items():
        print(f"  {k}: low {v[0] - 100:+.0f}%, end {v[1] - 100:+.0f}%")
    fig_fr_mechanism(spy_ratio)
    fig_pca_spectrum(con)
    fig_title_strip(con)
    con.close()


if __name__ == "__main__":
    main()
