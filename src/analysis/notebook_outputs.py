"""Notebook display helpers for scripted analysis outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from IPython.display import Image, display

CORRELATION_REGIMES = ["calm", "stress", "stress_minus_calm"]
CORRELATION_METRIC_COLUMNS = [
    "avg_corr_calm",
    "avg_corr_stress",
    "avg_corr_diff",
    "median_corr_calm",
    "median_corr_stress",
    "median_corr_diff",
    "p10_corr_calm",
    "p10_corr_stress",
    "p10_corr_diff",
    "p90_corr_calm",
    "p90_corr_stress",
    "p90_corr_diff",
    "min_corr_calm",
    "min_corr_stress",
    "max_corr_calm",
    "max_corr_stress",
]
PCA_METRIC_COLUMNS = [
    "stress_share",
    "pc1_share",
    "pc2_share",
    "top_3_share",
    "top_5_share",
    "effective_bets",
    "calm_pc1_share",
    "stress_pc1_share",
    "stress_minus_calm_pc1_share",
    "calm_effective_bets",
    "stress_effective_bets",
    "stress_minus_calm_effective_bets",
]
FORBES_RIGOBON_METRIC_COLUMNS = [
    "corr_calm",
    "corr_stress",
    "delta_corr",
    "fr_delta_asset_i",
    "fr_delta_asset_j",
    "fr_delta_spy",
    "fr_delta_used",
    "corr_stress_adjusted",
    "delta_corr_adjusted",
    "avg_delta_corr",
    "median_delta_corr",
    "avg_delta_corr_adjusted",
    "median_delta_corr_adjusted",
]


def notebook_project_root() -> Path:
    """Return the project root whether the notebook runs from root or notebooks/."""
    current = Path.cwd()
    return current.parent if current.name == "notebooks" else current


def get_available_tables(con) -> set[str]:
    """Return DuckDB table names for simple notebook checks."""
    return set(con.execute("SHOW TABLES").fetchdf()["name"])


def load_duckdb_table(con, table_name: str, order_by: str | None = None) -> pd.DataFrame:
    """Load a precomputed DuckDB table with a clear missing-table error."""
    available_tables = get_available_tables(con)
    if table_name not in available_tables:
        raise ValueError(f"Missing DuckDB table: {table_name}. Run the pipeline scripts first.")

    order_sql = f" ORDER BY {order_by}" if order_by else ""
    return con.execute(f"SELECT * FROM {table_name}{order_sql}").fetchdf()


def rounded_display(df: pd.DataFrame, metric_columns: list[str], decimals: int = 4) -> pd.DataFrame:
    """Return a copy with selected numeric columns rounded for display."""
    display_df = df.copy()
    columns = [column for column in metric_columns if column in display_df.columns]
    display_df[columns] = display_df[columns].round(decimals)
    return display_df


def format_correlation_summary(summary: pd.DataFrame) -> pd.DataFrame:
    """Format the canonical correlation summary table."""
    return rounded_display(summary, CORRELATION_METRIC_COLUMNS)


def format_pca_summary(summary: pd.DataFrame) -> pd.DataFrame:
    """Format the PCA concentration summary table."""
    return rounded_display(summary, PCA_METRIC_COLUMNS)


def format_pca_comparison(comparison: pd.DataFrame) -> pd.DataFrame:
    """Format the PCA calm-vs-stress comparison table."""
    return rounded_display(comparison, PCA_METRIC_COLUMNS)


def format_forbes_rigobon_table(table: pd.DataFrame) -> pd.DataFrame:
    """Format Forbes-Rigobon adjusted output tables."""
    return rounded_display(table, FORBES_RIGOBON_METRIC_COLUMNS)


def correlation_matrix_from_pairs(
    pair_table: pd.DataFrame,
    universe: str,
    regime: str,
) -> pd.DataFrame:
    """Rebuild a display matrix from unique pair rows."""
    subset = pair_table[
        (pair_table["universe"] == universe) & (pair_table["regime"] == regime)
    ].copy()
    if subset.empty:
        raise ValueError(f"No correlation pairs found for {universe} / {regime}.")

    assets = sorted(set(subset["asset_i"]).union(set(subset["asset_j"])))
    diagonal = 0.0 if regime == "stress_minus_calm" else 1.0
    matrix = pd.DataFrame(diagonal, index=assets, columns=assets, dtype=float)

    for row in subset.itertuples(index=False):
        matrix.loc[row.asset_i, row.asset_j] = row.correlation
        matrix.loc[row.asset_j, row.asset_i] = row.correlation

    return matrix


def label_correlation_breakdown(delta_corr: float) -> str:
    """Simple label for stress-minus-calm correlation changes."""
    if delta_corr >= 0.25:
        return "Strong breakdown"
    if delta_corr >= 0.10:
        return "Moderate breakdown"
    if delta_corr >= 0.00:
        return "Small increase"
    return "Correlation decreased"


def top_correlation_changes(
    pair_table: pd.DataFrame,
    universe: str,
    n: int = 20,
) -> pd.DataFrame:
    """Build rounded top pair rows sorted by stress-minus-calm correlation."""
    ranking = pairwise_table_from_pairs(pair_table, universe)

    display_cols = ["corr_calm", "corr_stress", "delta_corr"]
    top = ranking.head(n).copy()
    top[display_cols] = top[display_cols].round(4)
    return top


def pairwise_table_from_pairs(pair_table: pd.DataFrame, universe: str) -> pd.DataFrame:
    """Build the full pair table used by the Forbes-Rigobon notebook section."""
    calm = pair_table.query("universe == @universe and regime == 'calm'")
    stress = pair_table.query("universe == @universe and regime == 'stress'")
    delta = pair_table.query("universe == @universe and regime == 'stress_minus_calm'")

    ranking = calm.merge(
        stress,
        on=["universe", "method", "asset_i", "asset_j"],
        suffixes=("_calm", "_stress"),
    )
    ranking = ranking.merge(
        delta[["universe", "method", "asset_i", "asset_j", "correlation"]],
        on=["universe", "method", "asset_i", "asset_j"],
    )
    ranking = ranking.rename(
        columns={
            "asset_i": "asset_1",
            "asset_j": "asset_2",
            "correlation_calm": "corr_calm",
            "correlation_stress": "corr_stress",
            "correlation": "delta_corr",
        }
    )
    ranking["interpretation"] = ranking["delta_corr"].map(label_correlation_breakdown)
    return ranking.sort_values("delta_corr", ascending=False).reset_index(drop=True)


def display_png(path: Path | str, width: int | None = None) -> None:
    """Display a PNG if it exists, otherwise print the missing path."""
    figure_path = Path(path)
    if figure_path.exists():
        display(Image(filename=str(figure_path), width=width))
    else:
        print(f"Missing figure: {figure_path}")
