"""Reusable helpers for regime-conditional correlation tables.

The orchestration script `scripts/07_build_regime_correlations.py` calls into
this module. Heatmap plotting lives in
`notebooks/03_correlation_raw_full_pipeline.ipynb`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --- constants ---------------------------------------------------------------

SUMMARY_TABLE = "correlation_summary"
PAIRS_TABLE = "correlation_pairs"
CORRELATION_METHOD = "pearson"

EXCLUDED_RETURN_COLUMNS = {"date", "ms_stress", "ms_prob_stress", "created_at"}


# --- private helpers ---------------------------------------------------------


def _table_exists(con, table_name: str) -> bool:
    tables = set(con.execute("SHOW TABLES").fetchdf()["name"])
    return table_name in tables


# --- public loaders ----------------------------------------------------------


def load_labeled_universe(con, table_name: str) -> tuple[pd.DataFrame, list[str]]:
    """Load one labeled wide return table as complete-case rows plus columns."""
    if not _table_exists(con, table_name):
        raise RuntimeError(f"{table_name} table not found.")

    raw = con.execute(f"SELECT * FROM {table_name} ORDER BY date").fetchdf()
    return_columns = select_return_columns(raw)
    data = prepare_labeled_returns(raw, return_columns)
    return data, return_columns


# --- pure transforms ---------------------------------------------------------


def select_return_columns(
    df: pd.DataFrame,
    excluded_columns: set[str] | None = None,
) -> list[str]:
    """Return numeric return columns after excluding date and regime metadata."""
    excluded = EXCLUDED_RETURN_COLUMNS if excluded_columns is None else excluded_columns
    return_columns = [column for column in df.columns if column not in excluded]
    if len(return_columns) < 2:
        raise RuntimeError("Need at least two return columns for correlation analysis.")
    non_numeric = [
        column
        for column in return_columns
        if not pd.api.types.is_numeric_dtype(df[column])
        or pd.api.types.is_bool_dtype(df[column])
    ]
    if non_numeric:
        names = ", ".join(non_numeric)
        raise RuntimeError(f"Return columns must be numeric and non-boolean: {names}")
    return return_columns


def common_complete_case_dates(
    df: pd.DataFrame,
    return_columns: list[str],
    *,
    regime_col: str = "ms_stress",
) -> pd.DatetimeIndex:
    """Return the dates on which every column in ``return_columns`` is observed.

    Defines the common balanced window so the portfolio-level aggregates of every
    universe are computed on the same trading days (see the methodology's
    balanced-panel discussion).
    """
    prepared = prepare_labeled_returns(df, list(return_columns), regime_col=regime_col)
    return pd.DatetimeIndex(prepared["date"].unique())


def prepare_labeled_returns(
    df: pd.DataFrame,
    return_columns: list[str],
    *,
    regime_col: str = "ms_stress",
    restrict_dates: pd.DatetimeIndex | None = None,
) -> pd.DataFrame:
    """Keep strict complete-case rows with valid binary regime labels.

    When ``restrict_dates`` is given, the complete-case sample is further limited
    to those dates (the common balanced window from
    :func:`common_complete_case_dates`).
    """
    required = {"date", regime_col, *return_columns}
    missing = required - set(df.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise RuntimeError(f"Missing required column(s): {missing_text}")
    if len(set(return_columns)) != len(return_columns):
        raise RuntimeError("return_columns contains duplicates.")

    non_numeric = [
        column
        for column in return_columns
        if not pd.api.types.is_numeric_dtype(df[column])
        or pd.api.types.is_bool_dtype(df[column])
    ]
    if non_numeric:
        names = ", ".join(non_numeric)
        raise RuntimeError(f"Return columns must be numeric and non-boolean: {names}")

    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])
    if data["date"].isna().any():
        raise RuntimeError("Labeled returns contain missing dates.")
    if data["date"].duplicated().any():
        raise RuntimeError("Labeled returns contain duplicate dates.")

    numeric_regime = pd.to_numeric(data[regime_col], errors="raise")
    values = set(numeric_regime.dropna().unique())
    if not values.issubset({0, 1}):
        raise RuntimeError(f"{regime_col} must contain only 0/1 values.")
    data[regime_col] = numeric_regime.astype("Int64")

    finite_returns = np.isfinite(data[return_columns].to_numpy(dtype=float))
    non_missing_returns = data[return_columns].notna().to_numpy()
    if not finite_returns[non_missing_returns].all():
        raise RuntimeError("Return columns contain infinite values.")

    complete = data.dropna(subset=[regime_col, *return_columns]).copy()
    if restrict_dates is not None:
        allowed_dates = pd.DatetimeIndex(pd.to_datetime(restrict_dates))
        if allowed_dates.isna().any():
            raise RuntimeError("restrict_dates contains missing dates.")
        complete = complete[complete["date"].isin(allowed_dates)].copy()
    if complete.empty:
        raise RuntimeError("No complete-case return rows available.")

    complete[regime_col] = complete[regime_col].astype(int)
    stress_days = int(complete[regime_col].sum())
    calm_days = int((complete[regime_col] == 0).sum())
    if stress_days < 2 or calm_days < 2:
        raise RuntimeError("Need at least two calm and two stress observations.")

    return (
        complete[["date", *return_columns, regime_col]]
        .sort_values("date", kind="stable")
        .reset_index(drop=True)
    )


def correlation_matrices(
    data: pd.DataFrame,
    return_columns: list[str],
    *,
    regime_col: str = "ms_stress",
    method: str = CORRELATION_METHOD,
) -> dict[str, pd.DataFrame]:
    """Compute calm, stress, and stress-minus-calm correlations."""
    if len(set(return_columns)) != len(return_columns):
        raise RuntimeError("return_columns contains duplicates.")
    required = {regime_col, *return_columns}
    missing = required - set(data.columns)
    if missing:
        names = ", ".join(sorted(missing))
        raise RuntimeError(f"Missing required column(s): {names}")
    if not np.isfinite(data[return_columns].to_numpy(dtype=float)).all():
        raise RuntimeError("Return data must be complete and finite.")

    calm = data.loc[data[regime_col] == 0, return_columns].corr(method=method)
    stress = data.loc[data[regime_col] == 1, return_columns].corr(method=method)
    difference = stress - calm
    matrices = {"calm": calm, "stress": stress, "stress_minus_calm": difference}

    for name, matrix in matrices.items():
        if matrix.empty:
            raise RuntimeError(f"{name} correlation matrix is empty.")
        if matrix.isna().all(axis=0).any() or matrix.isna().all(axis=1).any():
            raise RuntimeError(f"{name} correlation matrix contains an all-null row or column.")
        if matrix.isna().any().any():
            raise RuntimeError(f"{name} correlation matrix contains missing values.")

    return matrices


def upper_triangle_values(matrix: pd.DataFrame) -> np.ndarray:
    """Return unique off-diagonal matrix values."""
    values = matrix.to_numpy(dtype=float)
    indices = np.triu_indices(values.shape[0], k=1)
    return values[indices]


def summary_from_matrices(
    matrices: dict[str, pd.DataFrame],
    *,
    universe: str,
    method: str,
    n_calm_days: int,
    n_stress_days: int,
) -> dict[str, float | int | str]:
    """Build the compact one-row summary used by the notebook."""
    calm_values = upper_triangle_values(matrices["calm"])
    stress_values = upper_triangle_values(matrices["stress"])
    diff_values = upper_triangle_values(matrices["stress_minus_calm"])
    n_assets = len(matrices["calm"])

    return {
        "universe": universe,
        "method": method,
        "n_assets": int(n_assets),
        "n_pairs": int(n_assets * (n_assets - 1) // 2),
        "n_calm_days": int(n_calm_days),
        "n_stress_days": int(n_stress_days),
        "avg_corr_calm": float(np.mean(calm_values)),
        "avg_corr_stress": float(np.mean(stress_values)),
        "avg_corr_diff": float(np.mean(diff_values)),
        "median_corr_calm": float(np.median(calm_values)),
        "median_corr_stress": float(np.median(stress_values)),
        "median_corr_diff": float(np.median(diff_values)),
        "p10_corr_calm": float(np.percentile(calm_values, 10)),
        "p10_corr_stress": float(np.percentile(stress_values, 10)),
        "p10_corr_diff": float(np.percentile(diff_values, 10)),
        "p90_corr_calm": float(np.percentile(calm_values, 90)),
        "p90_corr_stress": float(np.percentile(stress_values, 90)),
        "p90_corr_diff": float(np.percentile(diff_values, 90)),
        "min_corr_calm": float(np.min(calm_values)),
        "min_corr_stress": float(np.min(stress_values)),
        "max_corr_calm": float(np.max(calm_values)),
        "max_corr_stress": float(np.max(stress_values)),
    }


def matrix_to_pairs(
    matrix: pd.DataFrame,
    *,
    universe: str,
    method: str,
    regime: str,
) -> pd.DataFrame:
    """Convert a symmetric matrix to unique off-diagonal pair rows."""
    rows = []
    assets = list(matrix.columns)
    for i, asset_i in enumerate(assets):
        for asset_j in assets[i + 1 :]:
            rows.append(
                {
                    "universe": universe,
                    "method": method,
                    "regime": regime,
                    "asset_i": asset_i,
                    "asset_j": asset_j,
                    "correlation": float(matrix.loc[asset_i, asset_j]),
                }
            )
    
    # print(pd.DataFrame(rows)) # debugging

    return pd.DataFrame(rows)


def matrices_to_pair_table(
    matrices: dict[str, pd.DataFrame],
    *,
    universe: str,
    method: str,
) -> pd.DataFrame:
    """Convert all regime matrices to one long pair table."""
    
    return pd.concat(
        [
            matrix_to_pairs(matrix, universe=universe, method=method, regime=regime)
            for regime, matrix in matrices.items()
        ],
        ignore_index=True,
    )


def label_correlation_breakdown(delta_corr: float) -> str:
    """Simple interpretation label for stress-minus-calm correlation changes."""
    if delta_corr >= 0.25:
        return "Strong breakdown"
    if delta_corr >= 0.10:
        return "Moderate breakdown"
    if delta_corr >= 0.00:
        return "Small increase"
    return "Correlation decreased"


def pair_ranking_from_pairs(pair_table: pd.DataFrame, universe: str) -> pd.DataFrame:
    """Build calm/stress/delta pair rows for notebook display and FR inputs."""
    calm = pair_table.query("universe == @universe and regime == 'calm'")
    stress = pair_table.query("universe == @universe and regime == 'stress'")
    delta = pair_table.query("universe == @universe and regime == 'stress_minus_calm'")

    ranking = calm.merge(
        stress,
        on=["universe", "method", "asset_i", "asset_j"],
        suffixes=("_calm", "_stress"),
    )
    ranking = ranking.merge(
        delta[
            [
                "universe",
                "method",
                "asset_i",
                "asset_j",
                "correlation",
            ]
        ],
        on=["universe", "method", "asset_i", "asset_j"],
    )
    ranking = ranking.rename(
        columns={
            "correlation_calm": "corr_calm",
            "correlation_stress": "corr_stress",
            "correlation": "delta_corr",
        }
    )
    ranking["interpretation"] = ranking["delta_corr"].map(label_correlation_breakdown)
    return ranking.sort_values("delta_corr", ascending=False).reset_index(drop=True)


# --- public actions ----------------------------------------------------------


def build_universe_correlation_outputs(
    data: pd.DataFrame,
    return_columns: list[str],
    universe: str,
    *,
    method: str = CORRELATION_METHOD,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the one-row summary and the long pair table for one universe."""
    matrices = correlation_matrices(data, return_columns, method=method)
    n_calm_days = int((data["ms_stress"] == 0).sum())
    n_stress_days = int((data["ms_stress"] == 1).sum())
    summary = pd.DataFrame(
        [
            summary_from_matrices(
                matrices,
                universe=universe,
                method=method,
                n_calm_days=n_calm_days,
                n_stress_days=n_stress_days,
            )
        ]
    )
    pairs = matrices_to_pair_table(matrices, universe=universe, method=method)
    return summary, pairs


def write_correlation_outputs(
    con,
    summary: pd.DataFrame,
    pairs: pd.DataFrame,
) -> None:
    """Insert correlation outputs into explicit-DDL tables. Schemas must exist."""
    con.execute(
        f"""
        INSERT OR IGNORE INTO {SUMMARY_TABLE} (
            universe,
            method,
            n_assets,
            n_pairs,
            n_calm_days,
            n_stress_days,
            avg_corr_calm,
            avg_corr_stress,
            avg_corr_diff,
            median_corr_calm,
            median_corr_stress,
            median_corr_diff,
            p10_corr_calm,
            p10_corr_stress,
            p10_corr_diff,
            p90_corr_calm,
            p90_corr_stress,
            p90_corr_diff,
            min_corr_calm,
            min_corr_stress,
            max_corr_calm,
            max_corr_stress
        )
        SELECT
            universe,
            method,
            n_assets,
            n_pairs,
            n_calm_days,
            n_stress_days,
            avg_corr_calm,
            avg_corr_stress,
            avg_corr_diff,
            median_corr_calm,
            median_corr_stress,
            median_corr_diff,
            p10_corr_calm,
            p10_corr_stress,
            p10_corr_diff,
            p90_corr_calm,
            p90_corr_stress,
            p90_corr_diff,
            min_corr_calm,
            min_corr_stress,
            max_corr_calm,
            max_corr_stress
        FROM summary
        """
    )

    con.execute(
        f"""
        INSERT OR IGNORE INTO {PAIRS_TABLE} (
            universe,
            method,
            regime,
            asset_i,
            asset_j,
            correlation
        )
        SELECT
            universe,
            method,
            regime,
            asset_i,
            asset_j,
            correlation
        FROM pairs
        """
    )
