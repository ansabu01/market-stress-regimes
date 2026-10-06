"""Export dashboard-ready Parquet files from existing project outputs.

This script is intentionally read-only with respect to the scientific pipeline:
it reads existing DuckDB tables and existing CSV side-products, then writes
dashboard-friendly Parquet files under app/data.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "lsr.duckdb"
APP_DATA_DIR = PROJECT_ROOT / "app" / "data"
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import settings  # noqa: E402
from analysis.pca_concentration import (  # noqa: E402
    common_complete_case_dates,
    compute_correlation_matrix,
    concentration_summary,
    load_labeled_return_table,
    pca_from_correlation_matrix,
    prepare_labeled_returns,
)

RETURN_COLUMNS = [
    "AGG",
    "DBC",
    "EEM",
    "EFA",
    "EWG",
    "EWJ",
    "EWU",
    "GLD",
    "HYG",
    "SHY",
    "SPY",
    "TLT",
    "USO",
    "VNQ",
]

ETF_RETURNS_TABLE = "etf_returns_monthly_markov_labeled"
ROLLING_WINDOW = 126
ROLLING_DIAGNOSTIC_LABEL = "exploratory dashboard diagnostic"
PCA_UNIVERSES = (
    ("panel_a_cross_asset", settings.PANEL_A),
    ("panel_b_international_equity", settings.PANEL_B),
    ("etf_assets", settings.ETF_ASSETS),
)
DEFAULT_ROLLING_PAIRS = (
    ("panel_a_cross_asset", "SPY", "TLT"),
    ("panel_a_cross_asset", "SPY", "HYG"),
    ("panel_a_cross_asset", "SPY", "GLD"),
    ("panel_a_cross_asset", "DBC", "VNQ"),
    ("panel_b_international_equity", "SPY", "EFA"),
    ("panel_b_international_equity", "EEM", "EFA"),
    ("panel_b_international_equity", "EWG", "EWU"),
    ("etf_assets", "SPY", "TLT"),
    ("etf_assets", "SPY", "HYG"),
    ("etf_assets", "HYG", "TLT"),
    ("etf_assets", "DBC", "VNQ"),
    ("etf_assets", "EEM", "EWJ"),
)

DB_EXPORTS = {
    "returns.parquet": f"""
        SELECT
            date,
            {", ".join(RETURN_COLUMNS)},
            ms_stress,
            ms_prob_stress
        FROM etf_returns_monthly_markov_labeled
        ORDER BY date
    """,
    "corr_pairs.parquet": """
        SELECT universe, method, regime, asset_i, asset_j, correlation
        FROM correlation_pairs
        ORDER BY universe, method, regime, asset_i, asset_j
    """,
    "pca_regime_concentration_summary.parquet": """
        SELECT
            universe,
            regime,
            observations,
            assets,
            stress_share,
            pc1_share,
            pc2_share,
            top_3_share,
            top_5_share,
            effective_bets
        FROM pca_regime_concentration_summary
        ORDER BY universe, regime
    """,
    "pca_summary.parquet": """
        SELECT
            universe,
            regime,
            observations,
            assets,
            stress_share,
            pc1_share,
            pc2_share,
            top_3_share,
            top_5_share,
            effective_bets
        FROM pca_regime_concentration_summary
        ORDER BY universe, regime
    """,
    "pca_regime_concentration_eigenvalues.parquet": """
        SELECT
            universe,
            regime,
            component,
            eigenvalue,
            explained_variance_share,
            cumulative_explained_variance_share
        FROM pca_regime_concentration_eigenvalues
        ORDER BY universe, regime, component
    """,
    "pca_eigenvalues.parquet": """
        SELECT
            universe,
            regime,
            component,
            eigenvalue,
            explained_variance_share,
            cumulative_explained_variance_share
        FROM pca_regime_concentration_eigenvalues
        ORDER BY universe, regime, component
    """,
    "pca_regime_concentration_comparison.parquet": """
        SELECT
            universe,
            calm_pc1_share,
            stress_pc1_share,
            stress_minus_calm_pc1_share,
            calm_effective_bets,
            stress_effective_bets,
            stress_minus_calm_effective_bets,
            more_concentrated_in_stress
        FROM pca_regime_concentration_comparison
        ORDER BY universe
    """,
    "pca_comparison.parquet": """
        SELECT
            universe,
            calm_pc1_share,
            stress_pc1_share,
            stress_minus_calm_pc1_share,
            calm_effective_bets,
            stress_effective_bets,
            stress_minus_calm_effective_bets,
            more_concentrated_in_stress
        FROM pca_regime_concentration_comparison
        ORDER BY universe
    """,
    "forbes_rigobon_adjusted_pairs.parquet": """
        SELECT
            universe,
            correlation_method,
            fr_method,
            source_asset,
            asset_i,
            asset_j,
            corr_calm,
            corr_stress,
            delta_corr,
            fr_delta_asset_i,
            fr_delta_asset_j,
            fr_delta_spy,
            fr_delta_used,
            corr_stress_adjusted,
            delta_corr_adjusted,
            interpretation
        FROM forbes_rigobon_adjusted_pairs
        ORDER BY universe, fr_method, asset_i, asset_j
    """,
    "forbes_rigobon_results.parquet": """
        SELECT
            universe,
            correlation_method,
            fr_method,
            source_asset,
            asset_i,
            asset_j,
            corr_calm,
            corr_stress,
            delta_corr,
            fr_delta_asset_i,
            fr_delta_asset_j,
            fr_delta_spy,
            fr_delta_used,
            corr_stress_adjusted,
            delta_corr_adjusted,
            interpretation
        FROM forbes_rigobon_adjusted_pairs
        ORDER BY universe, fr_method, asset_i, asset_j
    """,
    "forbes_rigobon_adjusted_summary.parquet": """
        SELECT
            universe,
            fr_method,
            adjusted_rows,
            available_rows,
            unavailable_rows,
            avg_delta_corr,
            median_delta_corr,
            avg_delta_corr_adjusted,
            median_delta_corr_adjusted,
            robust_breakdown_count,
            volatility_bias_sensitive_count,
            resilient_decreased_count,
            mostly_resilient_count,
            adjustment_unavailable_count
        FROM forbes_rigobon_adjusted_summary
        ORDER BY universe, fr_method
    """,
    "forbes_rigobon_variance_ratios.parquet": """
        SELECT
            universe,
            asset,
            calm_variance,
            stress_variance,
            variance_ratio,
            fr_delta
        FROM forbes_rigobon_variance_ratios
        ORDER BY universe, asset
    """,
}

CSV_EXPORTS = {
    "bootstrap_pair_results.parquet": (
        PROJECT_ROOT
        / "outputs"
        / "04_correlation_bootstrapping"
        / "correlation_bootstrap_pair_results.csv"
    ),
    "stress_episode_all_pairs_broad.parquet": (
        PROJECT_ROOT / "outputs" / "tables" / "stress_episode_all_pairs_broad.csv"
    ),
    "stress_episode_all_pairs_granular.parquet": (
        PROJECT_ROOT / "outputs" / "tables" / "stress_episode_all_pairs_granular.csv"
    ),
    "stress_episode_pair_heterogeneity_ranking.parquet": (
        PROJECT_ROOT / "outputs" / "tables" / "stress_episode_pair_heterogeneity_ranking.csv"
    ),
    "markov_chain_transition_matrix.parquet": (
        PROJECT_ROOT / "outputs" / "02_regimes" / "markov_chain_transition_matrix.csv"
    ),
}

PAIR_RANKING_SOURCES = [
    PROJECT_ROOT / "outputs" / "03_correlation_raw" / "panel_a_cross_asset_pair_ranking.csv",
    PROJECT_ROOT
    / "outputs"
    / "03_correlation_raw"
    / "panel_b_international_equity_pair_ranking.csv",
    PROJECT_ROOT / "outputs" / "03_correlation_raw" / "etf_assets_pair_ranking.csv",
]

REGIME_TIMESERIES_QUERY = """
    WITH spy AS (
        SELECT date, price AS spy_adj_close
        FROM asset_prices
        WHERE ticker = 'SPY' AND price_source = 'adj_close'
    ),
    monthly AS (
        SELECT
            month_end,
            ms_prob_stress AS ms_prob_stress_monthly,
            ms_stress_50 AS ms_stress_50_monthly,
            ms_stress_75 AS ms_stress_75_monthly
        FROM markov_regime_monthly
    ),
    weekly_ranges AS (
        SELECT
            LAG(week_end) OVER (ORDER BY week_end) AS previous_week_end,
            week_end,
            ms_prob_stress AS ms_prob_stress_weekly,
            ms_stress_50 AS ms_stress_50_weekly,
            ms_stress_75 AS ms_stress_75_weekly
        FROM markov_regime_weekly
    )
    SELECT
        spy.date,
        spy.spy_adj_close,
        monthly.month_end AS markov_month_end,
        monthly.ms_prob_stress_monthly,
        monthly.ms_stress_50_monthly,
        monthly.ms_stress_75_monthly,
        weekly_ranges.week_end AS markov_week_end,
        weekly_ranges.ms_prob_stress_weekly,
        weekly_ranges.ms_stress_50_weekly,
        weekly_ranges.ms_stress_75_weekly,
        regime_labels.vix_close_adj,
        regime_labels.vix_q75_252,
        regime_labels.spx_close_adj,
        regime_labels.spx_rollmax_252,
        regime_labels.spx_drawdown,
        regime_labels.stress_raw,
        regime_labels.stress_smooth_21d,
        regime_labels.regime AS rule_based_regime
    FROM spy
    LEFT JOIN monthly
        ON DATE_TRUNC('month', spy.date) = DATE_TRUNC('month', monthly.month_end)
    LEFT JOIN weekly_ranges
        ON spy.date <= weekly_ranges.week_end
        AND spy.date > COALESCE(
            weekly_ranges.previous_week_end,
            weekly_ranges.week_end - INTERVAL 7 DAY
        )
    LEFT JOIN regime_labels
        ON spy.date = regime_labels.date
    ORDER BY spy.date
"""

REQUIRED_TABLES = {
    "asset_prices",
    "regime_labels",
    "markov_regime_monthly",
    "markov_regime_weekly",
    "etf_returns_monthly_markov_labeled",
    "correlation_pairs",
    "pca_regime_concentration_summary",
    "pca_regime_concentration_eigenvalues",
    "pca_regime_concentration_comparison",
    "forbes_rigobon_adjusted_pairs",
    "forbes_rigobon_adjusted_summary",
    "forbes_rigobon_variance_ratios",
}


def sql_literal(path: Path) -> str:
    """Return a DuckDB-safe SQL string literal for a filesystem path."""
    normalized = str(path).replace("\\", "/").replace("'", "''")
    return f"'{normalized}'"


def remove_existing(path: Path) -> None:
    """Remove a previous export so COPY can write a fresh Parquet file."""
    if path.exists():
        path.unlink()


def copy_query_to_parquet(
    con: duckdb.DuckDBPyConnection,
    query: str,
    output_name: str,
) -> Path:
    """Write a query result to app/data as Parquet."""
    output_path = APP_DATA_DIR / output_name
    remove_existing(output_path)
    con.execute(
        f"""
        COPY (
            {query.strip()}
        )
        TO {sql_literal(output_path)}
        (FORMAT PARQUET)
        """
    )
    return output_path


def copy_csv_to_parquet(
    con: duckdb.DuckDBPyConnection,
    source_path: Path,
    output_name: str,
) -> Path:
    """Write an existing CSV side-product to app/data as Parquet."""
    if not source_path.exists():
        raise FileNotFoundError(f"Missing required dashboard source CSV: {source_path}")

    output_path = APP_DATA_DIR / output_name
    remove_existing(output_path)
    con.execute(
        f"""
        COPY (
            SELECT *
            FROM read_csv_auto({sql_literal(source_path)}, HEADER = TRUE)
        )
        TO {sql_literal(output_path)}
        (FORMAT PARQUET)
        """
    )
    return output_path


def copy_dataframe_to_parquet(
    con: duckdb.DuckDBPyConnection,
    frame: pd.DataFrame,
    output_name: str,
) -> Path:
    """Write an in-memory dashboard diagnostic frame to app/data as Parquet."""
    if frame.empty:
        raise RuntimeError(f"Refusing to export empty optional diagnostic: {output_name}")

    output_path = APP_DATA_DIR / output_name
    remove_existing(output_path)
    temp_view = f"dashboard_export_{output_name.replace('.', '_')}"
    con.register(temp_view, frame)
    try:
        con.execute(
            f"""
            COPY (
                SELECT *
                FROM {temp_view}
            )
            TO {sql_literal(output_path)}
            (FORMAT PARQUET)
            """
        )
    finally:
        con.unregister(temp_view)
    return output_path


def copy_pair_rankings_to_parquet(con: duckdb.DuckDBPyConnection) -> Path:
    """Union existing per-universe pair ranking CSVs into one dashboard export."""
    missing = [path for path in PAIR_RANKING_SOURCES if not path.exists()]
    if missing:
        missing_text = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing pair-ranking source CSV(s): {missing_text}")

    output_path = APP_DATA_DIR / "pair_ranking.parquet"
    remove_existing(output_path)
    union_query = "\nUNION ALL\n".join(
        f"SELECT * FROM read_csv_auto({sql_literal(path)}, HEADER = TRUE)"
        for path in PAIR_RANKING_SOURCES
    )
    con.execute(
        f"""
        COPY (
            {union_query}
        )
        TO {sql_literal(output_path)}
        (FORMAT PARQUET)
        """
    )
    return output_path


def load_dashboard_returns(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Load stored labeled ETF returns for optional rolling dashboard diagnostics."""
    selected_columns = ["date", *RETURN_COLUMNS, "ms_stress", "ms_prob_stress"]
    query = f"""
        SELECT {", ".join(selected_columns)}
        FROM {ETF_RETURNS_TABLE}
        ORDER BY date
    """
    returns = con.execute(query).fetchdf()
    if returns.empty:
        raise RuntimeError(f"{ETF_RETURNS_TABLE} is empty.")

    returns["date"] = pd.to_datetime(returns["date"])
    for column in RETURN_COLUMNS:
        returns[column] = pd.to_numeric(returns[column], errors="coerce")
    return returns


def build_rolling_pair_correlations(returns: pd.DataFrame) -> pd.DataFrame:
    """Create rolling correlations for the default dashboard pair set."""
    rows = []
    available_columns = set(returns.columns)

    for universe, asset_i, asset_j in DEFAULT_ROLLING_PAIRS:
        if asset_i not in available_columns or asset_j not in available_columns:
            continue

        pair_data = (
            returns[["date", asset_i, asset_j]]
            .dropna(subset=[asset_i, asset_j])
            .sort_values("date", kind="stable")
            .reset_index(drop=True)
        )
        if len(pair_data) < ROLLING_WINDOW:
            continue

        rolling_corr = pair_data[asset_i].rolling(
            window=ROLLING_WINDOW,
            min_periods=ROLLING_WINDOW,
        ).corr(pair_data[asset_j])
        window_start = pair_data["date"].shift(ROLLING_WINDOW - 1)
        result = pd.DataFrame(
            {
                "date": pair_data["date"],
                "window_start": window_start,
                "window_end": pair_data["date"],
                "window": ROLLING_WINDOW,
                "universe": universe,
                "method": "pearson",
                "asset_i": asset_i,
                "asset_j": asset_j,
                "rolling_correlation": rolling_corr,
                "observations": ROLLING_WINDOW,
                "diagnostic_label": ROLLING_DIAGNOSTIC_LABEL,
            }
        ).dropna(subset=["rolling_correlation", "window_start"])
        rows.append(result)

    if not rows:
        return pd.DataFrame(
            columns=[
                "date",
                "window_start",
                "window_end",
                "window",
                "universe",
                "method",
                "asset_i",
                "asset_j",
                "rolling_correlation",
                "observations",
                "diagnostic_label",
            ]
        )

    return pd.concat(rows, ignore_index=True)


def build_rolling_absorption_ratio(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Create rolling PCA concentration diagnostics from rolling correlation matrices."""
    raw_data = load_labeled_return_table(con, ETF_RETURNS_TABLE)
    common_dates = common_complete_case_dates(raw_data, list(settings.ETF_ASSETS))
    rows = []

    for universe, requested_columns in PCA_UNIVERSES:
        data, return_columns = prepare_labeled_returns(
            raw_data,
            list(requested_columns),
            source_name=f"{ETF_RETURNS_TABLE}/{universe}/rolling-dashboard",
            restrict_dates=common_dates,
        )
        data = data.sort_values("date", kind="stable").reset_index(drop=True)
        if len(data) < ROLLING_WINDOW:
            continue

        for end_position in range(ROLLING_WINDOW - 1, len(data)):
            window = data.iloc[end_position - ROLLING_WINDOW + 1 : end_position + 1]
            corr = compute_correlation_matrix(window[return_columns])
            eigenvalues = pca_from_correlation_matrix(corr)
            summary = concentration_summary(eigenvalues)
            rows.append(
                {
                    "date": window["date"].iloc[-1],
                    "window_start": window["date"].iloc[0],
                    "window_end": window["date"].iloc[-1],
                    "window": ROLLING_WINDOW,
                    "universe": universe,
                    "observations": len(window),
                    "assets": len(return_columns),
                    "stress_share": float(window["ms_stress"].mean()),
                    "pc1_share": summary["pc1_share"],
                    "pc2_share": summary["pc2_share"],
                    "top_3_share": summary["top_3_share"],
                    "top_5_share": summary["top_5_share"],
                    "effective_bets": summary["effective_bets"],
                    "diagnostic_label": ROLLING_DIAGNOSTIC_LABEL,
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "date",
                "window_start",
                "window_end",
                "window",
                "universe",
                "observations",
                "assets",
                "stress_share",
                "pc1_share",
                "pc2_share",
                "top_3_share",
                "top_5_share",
                "effective_bets",
                "diagnostic_label",
            ]
        )

    return pd.DataFrame(rows)


def require_database_inputs(con: duckdb.DuckDBPyConnection) -> None:
    """Fail early if a required upstream table is missing."""
    existing_tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    missing = sorted(REQUIRED_TABLES - existing_tables)
    if missing:
        raise RuntimeError(
            "Missing required DuckDB table(s): "
            + ", ".join(missing)
            + ". Run the existing pipeline before exporting dashboard data."
        )


def export_dashboard_data() -> list[Path]:
    """Create all dashboard Parquet exports and return their paths."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing DuckDB database: {DB_PATH}")

    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        require_database_inputs(con)
        written.append(
            copy_query_to_parquet(
                con,
                REGIME_TIMESERIES_QUERY,
                "regime_timeseries.parquet",
            )
        )

        for output_name, query in DB_EXPORTS.items():
            written.append(copy_query_to_parquet(con, query, output_name))

        for output_name, source_path in CSV_EXPORTS.items():
            written.append(copy_csv_to_parquet(con, source_path, output_name))

        written.append(copy_pair_rankings_to_parquet(con))

        returns = load_dashboard_returns(con)
        rolling_pairs = build_rolling_pair_correlations(returns)
        if rolling_pairs.empty:
            print("Skipped rolling_pair_correlations.parquet: no eligible rolling pair windows.")
        else:
            written.append(
                copy_dataframe_to_parquet(
                    con,
                    rolling_pairs,
                    "rolling_pair_correlations.parquet",
                )
            )

        rolling_absorption = build_rolling_absorption_ratio(con)
        if rolling_absorption.empty:
            print("Skipped rolling_absorption_ratio.parquet: no eligible rolling PCA windows.")
        else:
            written.append(
                copy_dataframe_to_parquet(
                    con,
                    rolling_absorption,
                    "rolling_absorption_ratio.parquet",
                )
            )

    return written


def main() -> None:
    written = export_dashboard_data()
    print(f"Exported {len(written)} dashboard parquet files to {APP_DATA_DIR}:")
    for path in sorted(written):
        print(f"  {path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
