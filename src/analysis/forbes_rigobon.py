"""Forbes-Rigobon calculations and database-table builders.

This module is the Forbes-Rigobon equivalent of ``markov_switching.py``:
the reusable calculation and data-preparation functions live here, while the
numbered script only executes them in the required order.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from analysis.regime_correlations import PAIRS_TABLE, prepare_labeled_returns


VARIANCE_RATIOS_TABLE = "forbes_rigobon_variance_ratios"
ADJUSTED_PAIRS_TABLE = "forbes_rigobon_adjusted_pairs"
ADJUSTED_SUMMARY_TABLE = "forbes_rigobon_adjusted_summary"

ROBUST_BREAKDOWN = "Robust breakdown after adjustment"
VOLATILITY_BIAS_SENSITIVE = "Volatility-bias-sensitive increase"
RESILIENT_DECREASED = "Resilient: correlation decreased in stress"
MOSTLY_RESILIENT = "Mostly resilient / small adjusted increase"
ADJUSTMENT_UNAVAILABLE = "Adjustment unavailable"


# This function calculates the relative variance change from the calm regime
# to the stress regime.
def variance_delta(
    variance_stress: np.ndarray | float,
    variance_calm: np.ndarray | float,
    *,
    clip: bool = True,
) -> np.ndarray | float:
    """Calculate the Forbes-Rigobon variance shock.

    The raw relative variance change is

    ``ratio - 1 = variance_stress / variance_calm - 1``.

    By default the shock is clipped at zero,

    ``delta = max(variance_stress / variance_calm - 1, 0)``,

    which is the definition used in the methodology and the only case classical
    Forbes-Rigobon (2002) is built for: the high-volatility regime can only carry
    *excess* variance, so the adjustment only ever deflates a volatility-inflated
    correlation. A negative raw shock (lower variance in stress) would instead
    make the denominator ``sqrt(1 + delta(1 - rho^2))`` fall below one and
    mechanically *inflate* the correlation, which is outside the framework; the
    clip rules that out. Pass ``clip=False`` to recover the signed raw shock for
    diagnostics (equivalently ``variance_ratio - 1``).

    Zero or missing calm variance makes the ratio undefined; those observations
    are returned as ``NaN`` instead of producing an infinite value.

    Parameters
    ----------
    variance_stress:
        Return variance measured during the stress regime.
    variance_calm:
        Return variance measured during the calm regime.
    clip:
        When ``True`` (default) floor the shock at zero per classical
        Forbes-Rigobon; when ``False`` return the signed raw shock.

    Returns
    -------
    numpy.ndarray or float
        The variance shock, with ``NaN`` for invalid observations.
    """
    stress = np.asarray(variance_stress, dtype=float)
    calm = np.asarray(variance_calm, dtype=float)
    valid = np.isfinite(stress) & np.isfinite(calm) & (calm > 0)

    with np.errstate(divide="ignore", invalid="ignore"):
        raw = stress / calm - 1.0
        if clip:
            raw = np.maximum(raw, 0.0)
        delta = np.where(valid, raw, np.nan)

    return float(delta) if delta.ndim == 0 else delta


# This function applies the SPY variance delta and is only used for ETF pairs
# that contain SPY.
def market_spy_adjustment(
    corr_stress: np.ndarray | float,
    spy_delta: np.ndarray | float,
) -> np.ndarray | float:
    """Adjust SPY-pair stress correlations using SPY as the source market.

    This adjustment is only applied to pairs where one asset is SPY. SPY is the
    natural source market because the stress regime is based on broad market
    stress and SPY is the risky-market benchmark.

    Parameters
    ----------
    corr_stress:
        Raw correlation observed for an ETF pair during the stress regime.
    spy_delta:
        SPY's stress-to-calm variance change from :func:`variance_delta`.

    Returns
    -------
    numpy.ndarray or float
        Forbes-Rigobon-adjusted stress correlation.
    """
    return _adjust_correlation(corr_stress, spy_delta)


# This function uses the larger ETF-specific variance delta for an unordered
# pair and therefore provides the conservative robustness check.
def pair_max_adjustment(
    corr_stress: np.ndarray | float,
    delta_i: np.ndarray | float,
    delta_j: np.ndarray | float,
) -> np.ndarray | float:
    """Adjust each unordered ETF pair with its larger variance delta.

    The function compares the stress-to-calm variance changes of both ETFs and
    uses ``max(delta_i, delta_j)``. This is the conservative robustness check:
    an increase that remains after this stronger correction is harder to
    explain as a mechanical consequence of higher volatility.

    If either ETF delta is missing, the result remains ``NaN`` because the
    larger of the two values cannot be established reliably.

    Parameters
    ----------
    corr_stress:
        Raw stress correlation of the unordered ETF pair.
    delta_i:
        Variance delta of the first ETF.
    delta_j:
        Variance delta of the second ETF.

    Returns
    -------
    numpy.ndarray or float
        Forbes-Rigobon-adjusted stress correlation using the larger delta.
    """
    first = np.asarray(delta_i, dtype=float)
    second = np.asarray(delta_j, dtype=float)
    valid = np.isfinite(first) & np.isfinite(second)
    pair_delta = np.where(valid, np.maximum(first, second), np.nan)
    return _adjust_correlation(corr_stress, pair_delta)


# This internal helper contains the common Forbes-Rigobon formula used by the
# public adjustment variants.
def _adjust_correlation(
    corr_stress: np.ndarray | float,
    delta: np.ndarray | float,
) -> np.ndarray | float:
    """Apply the common Forbes-Rigobon correlation formula."""
    correlation = np.asarray(corr_stress, dtype=float)
    variance_change = np.asarray(delta, dtype=float)

    with np.errstate(divide="ignore", invalid="ignore"):
        denominator = np.sqrt(
            1.0 + variance_change * (1.0 - correlation**2)
        )
        adjusted = correlation / denominator

    valid = (
        np.isfinite(correlation)
        & np.isfinite(variance_change)
        & np.isfinite(adjusted)
        & (np.abs(correlation) <= 1.0)
    )
    adjusted = np.where(valid, adjusted, np.nan)
    return float(adjusted) if adjusted.ndim == 0 else adjusted


# This function checks whether a specific table exists in DuckDB.
def table_exists(con, table_name: str) -> bool:
    """Return whether a table is present in the connected DuckDB database."""
    return table_name in set(con.execute("SHOW TABLES").fetchdf()["name"])


# This function loads the calm, stress, and difference correlations already
# calculated by script 07 and reshapes them to one row per ETF pair.
def load_raw_correlations(con, universe: str) -> pd.DataFrame:
    """Load stored raw correlations without calculating correlations again.

    The long ``correlation_pairs`` table contains one row per regime. This
    function pivots the three required regimes into ``corr_calm``,
    ``corr_stress``, and ``delta_corr`` columns.
    """
    if not table_exists(con, PAIRS_TABLE):
        raise RuntimeError(
            f"{PAIRS_TABLE} is missing. Run scripts/07_build_regime_correlations.py first."
        )

    pairs = con.execute(
        f"""
        SELECT
            universe,
            method AS correlation_method,
            asset_i,
            asset_j,
            MAX(CASE WHEN regime = 'calm' THEN correlation END) AS corr_calm,
            MAX(CASE WHEN regime = 'stress' THEN correlation END) AS corr_stress,
            MAX(
                CASE WHEN regime = 'stress_minus_calm' THEN correlation END
            ) AS delta_corr
        FROM {PAIRS_TABLE}
        WHERE universe = ?
        GROUP BY universe, method, asset_i, asset_j
        ORDER BY asset_i, asset_j
        """,
        [universe],
    ).fetchdf()

    required = ["corr_calm", "corr_stress", "delta_corr"]
    if pairs.empty:
        raise RuntimeError(f"No stored correlation pairs found for {universe}.")
    if pairs[required].isna().any().any():
        raise RuntimeError(f"Stored correlation rows are incomplete for {universe}.")
    return pairs


# This function calculates the calm variance, stress variance, and resulting
# Forbes-Rigobon delta for every ETF.
def calculate_variance_table(
    data: pd.DataFrame,
    return_columns: list[str],
    universe: str,
    regime_col: str = "ms_stress",
) -> pd.DataFrame:
    """Build one variance-ratio row per ETF from regime-labelled returns."""
    calm_variance = data.loc[data[regime_col] == 0, return_columns].var()
    stress_variance = data.loc[data[regime_col] == 1, return_columns].var()
    calm_values = calm_variance.reindex(return_columns).to_numpy()
    stress_values = stress_variance.reindex(return_columns).to_numpy()

    return pd.DataFrame(
        {
            "universe": universe,
            "asset": return_columns,
            "calm_variance": calm_values,
            "stress_variance": stress_values,
            "variance_ratio": np.divide(
                stress_values,
                calm_values,
                out=np.full(len(return_columns), np.nan),
                where=calm_values > 0,
            ),
            "fr_delta": variance_delta(stress_values, calm_values),
        }
    )


# This function attaches both ETF-specific deltas and the SPY delta used by the
# main method to every raw correlation pair.
def _attach_variance_deltas(
    raw_pairs: pd.DataFrame,
    variance_ratios: pd.DataFrame,
) -> tuple[pd.DataFrame, float]:
    """Attach ETF variance deltas to pair rows and return the SPY delta."""
    delta_by_asset = variance_ratios.set_index("asset")["fr_delta"]
    pairs = raw_pairs.copy()
    pairs["fr_delta_asset_i"] = pairs["asset_i"].map(delta_by_asset)
    pairs["fr_delta_asset_j"] = pairs["asset_j"].map(delta_by_asset)

    spy_matches = variance_ratios.loc[variance_ratios["asset"] == "SPY", "fr_delta"]
    spy_delta = float(spy_matches.iloc[0]) if not spy_matches.empty else np.nan
    pairs["fr_delta_spy"] = spy_delta
    return pairs, spy_delta


# This function translates the raw and adjusted correlation changes into an
# interpretable result category for later reporting.
def interpretation_label(delta_raw: float, delta_adjusted: float) -> str:
    """Classify whether a raw correlation increase survives adjustment."""
    if pd.isna(delta_adjusted):
        return ADJUSTMENT_UNAVAILABLE
    if delta_raw < 0:
        return RESILIENT_DECREASED
    if delta_raw >= 0.10 and delta_adjusted >= 0.10:
        return ROBUST_BREAKDOWN
    if delta_raw >= 0.10:
        return VOLATILITY_BIAS_SENSITIVE
    return MOSTLY_RESILIENT


# This helper converts the result of one adjustment method into the common
# database-table format.
def _finalize_method(
    pairs: pd.DataFrame,
    *,
    method: str,
    source_asset,
    delta_used,
    adjusted_correlation,
) -> pd.DataFrame:
    """Add method metadata, adjusted changes, and interpretation labels."""
    result = pairs.copy()
    result["fr_method"] = method
    result["source_asset"] = source_asset
    result["fr_delta_used"] = delta_used
    result["corr_stress_adjusted"] = adjusted_correlation
    result["delta_corr_adjusted"] = result["corr_stress_adjusted"] - result["corr_calm"]
    result["interpretation"] = [
        interpretation_label(raw, adjusted)
        for raw, adjusted in zip(
            result["delta_corr"],
            result["delta_corr_adjusted"],
        )
    ]
    return result


# This function creates the two Forbes-Rigobon outputs used in the analysis:
# SPY adjustment for SPY pairs and pair-max adjustment for every pair.
def build_adjusted_pairs(
    raw_pairs: pd.DataFrame,
    variance_ratios: pd.DataFrame,
) -> pd.DataFrame:
    """Build all adjusted pair rows while retaining the stored raw values."""
    pairs, spy_delta = _attach_variance_deltas(raw_pairs, variance_ratios)

    spy_pair = (pairs["asset_i"] == "SPY") | (pairs["asset_j"] == "SPY")
    spy_pairs = pairs.loc[spy_pair].copy()
    market_spy = _finalize_method(
        spy_pairs,
        method="market_spy",
        source_asset="SPY",
        delta_used=spy_delta,
        adjusted_correlation=market_spy_adjustment(
            spy_pairs["corr_stress"],
            spy_delta,
        ),
    )

    valid_pair_delta = (
        pairs[["fr_delta_asset_i", "fr_delta_asset_j"]].notna().all(axis=1)
    )
    pair_delta = pairs[["fr_delta_asset_i", "fr_delta_asset_j"]].max(
        axis=1,
        skipna=False,
    )
    pair_source = np.where(
        pairs["fr_delta_asset_i"] >= pairs["fr_delta_asset_j"],
        pairs["asset_i"],
        pairs["asset_j"],
    )
    pair_source = pd.Series(pair_source, index=pairs.index).where(valid_pair_delta)
    pair_max = _finalize_method(
        pairs,
        method="pair_max",
        source_asset=pair_source,
        delta_used=pair_delta,
        adjusted_correlation=pair_max_adjustment(
            pairs["corr_stress"],
            pairs["fr_delta_asset_i"],
            pairs["fr_delta_asset_j"],
        ),
    )

    columns = [
        "universe",
        "correlation_method",
        "fr_method",
        "source_asset",
        "asset_i",
        "asset_j",
        "corr_calm",
        "corr_stress",
        "delta_corr",
        "fr_delta_asset_i",
        "fr_delta_asset_j",
        "fr_delta_spy",
        "fr_delta_used",
        "corr_stress_adjusted",
        "delta_corr_adjusted",
        "interpretation",
    ]
    return pd.concat(
        [market_spy, pair_max],
        ignore_index=True,
    )[columns]


# This function summarizes pair-level results by adjustment method so the
# methods can be compared compactly in the report.
def build_summary(adjusted_pairs: pd.DataFrame) -> pd.DataFrame:
    """Summarize availability, changes, and classifications by FR method."""
    rows = []
    for (universe, method), group in adjusted_pairs.groupby(["universe", "fr_method"]):
        rows.append(
            {
                "universe": universe,
                "fr_method": method,
                "adjusted_rows": len(group),
                "available_rows": int(group["corr_stress_adjusted"].notna().sum()),
                "unavailable_rows": int(group["corr_stress_adjusted"].isna().sum()),
                "avg_delta_corr": group["delta_corr"].mean(),
                "median_delta_corr": group["delta_corr"].median(),
                "avg_delta_corr_adjusted": group["delta_corr_adjusted"].mean(),
                "median_delta_corr_adjusted": group["delta_corr_adjusted"].median(),
                "robust_breakdown_count": int(
                    (group["interpretation"] == ROBUST_BREAKDOWN).sum()
                ),
                "volatility_bias_sensitive_count": int(
                    (group["interpretation"] == VOLATILITY_BIAS_SENSITIVE).sum()
                ),
                "resilient_decreased_count": int(
                    (group["interpretation"] == RESILIENT_DECREASED).sum()
                ),
                "mostly_resilient_count": int(
                    (group["interpretation"] == MOSTLY_RESILIENT).sum()
                ),
                "adjustment_unavailable_count": int(
                    (group["interpretation"] == ADJUSTMENT_UNAVAILABLE).sum()
                ),
            }
        )
    return pd.DataFrame(rows)


# This function builds the variance, pair, and summary tables for several
# universes at once, mirroring the PCA multi-universe builder.
def build_all_forbes_rigobon_outputs(
    con,
    raw_labeled: pd.DataFrame,
    universes: list[tuple[str, list[str]]],
    *,
    restrict_dates=None,
    regime_col: str = "ms_stress",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build Forbes-Rigobon outputs for every universe on one shared window.

    For each ``(universe, requested_columns)`` entry the variance ratios are
    computed from ``raw_labeled`` restricted to ``restrict_dates`` (the common
    balanced window), so the variance shocks and the stored raw correlations they
    adjust are measured on identical trading days. The raw correlations
    themselves are loaded from the ``correlation_pairs`` table and never
    recalculated.

    Returns the concatenated ``(variance_ratios, adjusted_pairs, summary)`` frames
    spanning all universes. ``summary`` is built once over the pooled pairs and
    therefore carries one row per ``(universe, fr_method)``.
    """
    variance_frames: list[pd.DataFrame] = []
    pair_frames: list[pd.DataFrame] = []

    for universe, requested_columns in universes:
        columns = [column for column in requested_columns if column in raw_labeled.columns]
        if len(columns) < 2:
            raise RuntimeError(f"Universe {universe} needs at least two available assets.")

        data = prepare_labeled_returns(
            raw_labeled,
            columns,
            regime_col=regime_col,
            restrict_dates=restrict_dates,
        )
        variance_ratios = calculate_variance_table(
            data,
            columns,
            universe=universe,
            regime_col=regime_col,
        )
        raw_pairs = load_raw_correlations(con, universe)
        adjusted_pairs = build_adjusted_pairs(raw_pairs, variance_ratios)

        variance_frames.append(variance_ratios)
        pair_frames.append(adjusted_pairs)

    all_variance = pd.concat(variance_frames, ignore_index=True)
    all_pairs = pd.concat(pair_frames, ignore_index=True)
    summary = build_summary(all_pairs)
    return all_variance, all_pairs, summary


# This function creates the main Forbes-Rigobon comparison plot from the stored
# pair-level results.
def plot_raw_vs_adjusted_changes(
    adjusted_pairs: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Compare raw and adjusted correlation changes for the two FR methods.

    Each point represents one unordered ETF pair. The horizontal coordinate is
    the raw stress-minus-calm correlation change and the vertical coordinate is
    the change after Forbes-Rigobon adjustment. Points below the diagonal were
    reduced by the volatility correction.

    Two panels are shown: ``market_spy`` for SPY pairs and ``pair_max`` as the
    conservative robustness check for all pairs.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    methods = [
        ("market_spy", "SPY-pair adjustment"),
        ("pair_max", "Pair-max robustness check"),
    ]
    figure_data = adjusted_pairs[
        adjusted_pairs["fr_method"].isin([method for method, _ in methods])
    ].dropna(subset=["delta_corr", "delta_corr_adjusted"])
    if figure_data.empty:
        raise ValueError("No valid market_spy or pair_max rows available for plotting.")

    lower = min(
        figure_data["delta_corr"].min(),
        figure_data["delta_corr_adjusted"].min(),
    )
    upper = max(
        figure_data["delta_corr"].max(),
        figure_data["delta_corr_adjusted"].max(),
    )
    padding = max((upper - lower) * 0.08, 0.02)
    limits = (lower - padding, upper + padding)

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharex=True, sharey=True)
    for ax, (method, title) in zip(axes, methods):
        rows = figure_data.loc[figure_data["fr_method"] == method]
        ax.scatter(
            rows["delta_corr"],
            rows["delta_corr_adjusted"],
            color="#2f6f9f",
            alpha=0.75,
            edgecolor="white",
            linewidth=0.4,
        )
        ax.plot(limits, limits, color="#666666", linestyle="--", linewidth=1.0)
        ax.axhline(0, color="#bbbbbb", linewidth=0.8)
        ax.axvline(0, color="#bbbbbb", linewidth=0.8)
        ax.set_title(title)
        ax.set_xlim(limits)
        ax.set_ylim(limits)
        ax.set_xlabel("Raw stress minus calm correlation")
        ax.grid(color="#eeeeee", linewidth=0.7)

    axes[0].set_ylabel("Adjusted stress minus calm correlation")
    fig.suptitle("Forbes-Rigobon adjustment of ETF correlation changes")
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


# This function writes variance values, pair results, and summary statistics to
# the three database tables created from the SQL schemas.
def write_outputs(
    con,
    variance_ratios: pd.DataFrame,
    adjusted_pairs: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    """Insert the prepared Forbes-Rigobon DataFrames into DuckDB."""
    variance_columns = [
        "universe",
        "asset",
        "calm_variance",
        "stress_variance",
        "variance_ratio",
        "fr_delta",
    ]
    variance_sql = ", ".join(variance_columns)
    con.execute(
        f"INSERT INTO {VARIANCE_RATIOS_TABLE} ({variance_sql}) "
        f"SELECT {variance_sql} FROM variance_ratios"
    )

    pair_columns = ", ".join(adjusted_pairs.columns)
    con.execute(
        f"INSERT INTO {ADJUSTED_PAIRS_TABLE} ({pair_columns}) "
        f"SELECT {pair_columns} FROM adjusted_pairs"
    )

    summary_columns = ", ".join(summary.columns)
    con.execute(
        f"INSERT INTO {ADJUSTED_SUMMARY_TABLE} ({summary_columns}) "
        f"SELECT {summary_columns} FROM summary"
    )
