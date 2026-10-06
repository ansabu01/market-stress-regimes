"""PCA concentration metrics from empirical correlation matrices."""

from __future__ import annotations

import numpy as np
import pandas as pd

EIGENVALUES_TABLE = "pca_regime_concentration_eigenvalues"
SUMMARY_TABLE = "pca_regime_concentration_summary"
COMPARISON_TABLE = "pca_regime_concentration_comparison"
EXCLUDED_RETURN_COLUMNS = {"date", "ms_stress", "ms_prob_stress", "created_at"}


def compute_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """Return a validated raw correlation matrix for complete-case returns."""
    if returns.empty:
        raise RuntimeError("Cannot compute PCA on an empty return sample.")
    if returns.shape[1] < 2:
        raise RuntimeError("Need at least two return columns for PCA.")

    corr = returns.corr()
    if corr.empty:
        raise RuntimeError("Correlation matrix is empty.")
    if corr.isna().all(axis=0).any() or corr.isna().all(axis=1).any():
        raise RuntimeError("Correlation matrix contains an all-null row or column.")
    if corr.isna().any().any():
        raise RuntimeError("Correlation matrix contains missing values.")

    return corr


def pca_from_correlation_matrix(corr: pd.DataFrame) -> pd.DataFrame:
    """Compute PCA eigenvalue shares from a raw correlation matrix."""
    values = corr.to_numpy(dtype=float)
    values = (values + values.T) / 2.0

    eigenvalues = np.linalg.eigvalsh(values)
    eigenvalues = np.sort(eigenvalues)[::-1]
    eigenvalues[np.isclose(eigenvalues, 0.0, atol=1e-10)] = 0.0
    if (eigenvalues < -1e-8).any():
        min_value = float(eigenvalues.min())
        raise RuntimeError(f"Correlation matrix has materially negative eigenvalues: {min_value}")

    eigenvalues = np.clip(eigenvalues, 0.0, None)
    total = float(eigenvalues.sum())
    if total <= 0:
        raise RuntimeError("Correlation matrix eigenvalues sum to zero.")

    explained_share = eigenvalues / total
    # Cumulative share is mathematically bounded by 1.0; clip floating-point
    # round-off so the SQL CHECK constraint (BETWEEN 0 AND 1) passes.
    cumulative_share = np.clip(np.cumsum(explained_share), 0.0, 1.0)
    return pd.DataFrame(
        {
            "component": np.arange(1, len(eigenvalues) + 1),
            "eigenvalue": eigenvalues,
            "explained_variance_share": explained_share,
            "cumulative_explained_variance_share": cumulative_share,
        }
    )


def effective_bets(explained_shares: pd.Series | np.ndarray) -> float:
    """Participation-ratio effective number of PCA directions."""
    shares = np.asarray(explained_shares, dtype=float)
    denominator = float(np.sum(shares**2))
    if denominator <= 0:
        raise RuntimeError("Cannot compute effective bets from zero eigenvalue shares.")
    return 1.0 / denominator


def concentration_summary(eigenvalues: pd.DataFrame) -> dict[str, float]:
    """Summarize PCA concentration from eigenvalue shares."""
    shares = eigenvalues["explained_variance_share"]
    return {
        "pc1_share": float(shares.iloc[0]),
        "pc2_share": float(shares.iloc[1]) if len(shares) > 1 else np.nan,
        "top_3_share": float(shares.head(3).sum()),
        "top_5_share": float(shares.head(5).sum()),
        "effective_bets": effective_bets(shares),
    }


def _table_exists(con, table_name: str) -> bool:
    tables = set(con.execute("SHOW TABLES").fetchdf()["name"])
    return table_name in tables


def _require_table_columns(
    con,
    table_name: str,
    required_columns: set[str],
) -> None:
    if not _table_exists(con, table_name):
        raise RuntimeError(f"{table_name} table not found.")

    columns = set(con.execute(f"DESCRIBE {table_name}").fetchdf()["column_name"])
    missing_columns = required_columns - columns
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise RuntimeError(f"{table_name} is missing required column(s): {missing}")


def _select_return_columns(
    data: pd.DataFrame,
    requested_return_columns: list[str] | None = None,
) -> list[str]:
    available_return_columns = [
        column for column in data.columns if column not in EXCLUDED_RETURN_COLUMNS
    ]
    if requested_return_columns is None:
        return_columns = available_return_columns
    else:
        return_columns = list(dict.fromkeys(requested_return_columns))
        missing_columns = set(return_columns) - set(data.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise RuntimeError(f"Labeled returns are missing requested column(s): {missing}")

    if len(return_columns) < 2:
        raise RuntimeError("Need at least two return columns for PCA.")
    return return_columns


def load_labeled_return_table(con, table_name: str) -> pd.DataFrame:
    """Load a labeled return table without applying universe-specific complete cases."""
    _require_table_columns(con, table_name, {"date", "ms_stress"})

    data = con.execute(f"SELECT * FROM {table_name} ORDER BY date").fetchdf()
    if data.empty:
        raise RuntimeError(f"{table_name} is empty.")

    data["date"] = pd.to_datetime(data["date"])
    return data


def common_complete_case_dates(
    data: pd.DataFrame,
    return_columns: list[str],
) -> pd.DatetimeIndex:
    """Return the dates on which every column in ``return_columns`` is observed.

    This defines the common balanced window: the trading days for which the
    whole (typically combined) universe is available. Restricting each panel to
    these dates puts every universe on the same calendar and the same stress/calm
    mix, so the cross-panel concentration comparison is apples-to-apples.
    """
    prepared, _ = prepare_labeled_returns(
        data, list(return_columns), source_name="common-window"
    )
    return pd.DatetimeIndex(prepared["date"].unique())


def prepare_labeled_returns(
    data: pd.DataFrame,
    return_columns: list[str] | None = None,
    *,
    source_name: str = "labeled returns",
    restrict_dates: pd.DatetimeIndex | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Return complete-case labeled returns for the requested PCA universe.

    When ``restrict_dates`` is given, the complete-case sample is further limited
    to those dates (the common balanced window from
    :func:`common_complete_case_dates`), so every universe is compared on the same
    trading days.
    """
    if "date" not in data.columns or "ms_stress" not in data.columns:
        raise RuntimeError(f"{source_name} must contain date and ms_stress columns.")

    data = data.copy()
    data["date"] = pd.to_datetime(data["date"])
    return_columns = _select_return_columns(data, return_columns)
    data["ms_stress"] = data["ms_stress"].astype("Int64")
    values = set(data["ms_stress"].dropna().astype(int).unique())
    if not values.issubset({0, 1}):
        raise RuntimeError(f"{source_name}.ms_stress must contain only 0/1 values.")

    complete = data.dropna(subset=["ms_stress", *return_columns]).copy()
    if restrict_dates is not None:
        complete = complete[complete["date"].isin(pd.DatetimeIndex(restrict_dates))].copy()
    if complete.empty:
        raise RuntimeError(f"{source_name} has no complete-case return rows.")
    if complete["date"].duplicated().any():
        raise RuntimeError(f"{source_name} contains duplicate dates.")

    complete["ms_stress"] = complete["ms_stress"].astype(int)
    stress_rows = int(complete["ms_stress"].sum())
    calm_rows = int((complete["ms_stress"] == 0).sum())
    if stress_rows < 2 or calm_rows < 2:
        raise RuntimeError(f"{source_name} needs at least two calm and stress rows.")

    return complete[["date", *return_columns, "ms_stress"]], return_columns


def load_labeled_returns(
    con,
    table_name: str,
    return_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Load complete-case labeled returns for PCA."""
    data = load_labeled_return_table(con, table_name)
    return prepare_labeled_returns(data, return_columns, source_name=table_name)


def pca_for_regime(
    data: pd.DataFrame,
    return_columns: list[str],
    *,
    universe: str,
    regime: str,
    stress_share: float,
) -> tuple[pd.DataFrame, dict[str, float | int | str]]:
    """Build eigenvalue rows and one summary row for a single regime sample."""
    corr = compute_correlation_matrix(data[return_columns])
    eigenvalues = pca_from_correlation_matrix(corr)
    eigenvalues["universe"] = universe
    eigenvalues["regime"] = regime
    eigenvalues = eigenvalues[
        [
            "universe",
            "regime",
            "component",
            "eigenvalue",
            "explained_variance_share",
            "cumulative_explained_variance_share",
        ]
    ]

    summary = {
        "universe": universe,
        "regime": regime,
        "observations": len(data),
        "assets": len(return_columns),
        "stress_share": stress_share,
        **concentration_summary(eigenvalues),
    }
    return eigenvalues, summary


def build_universe_outputs(
    universe: str,
    data: pd.DataFrame,
    return_columns: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build all PCA outputs for one return universe."""
    stress_share = float(data["ms_stress"].mean())
    regime_samples = {
        "full": data,
        "calm": data.loc[data["ms_stress"] == 0],
        "stress": data.loc[data["ms_stress"] == 1],
    }

    eigenvalue_frames = []
    summary_rows = []
    for regime, sample in regime_samples.items():
        eigenvalues, summary = pca_for_regime(
            sample,
            return_columns,
            universe=universe,
            regime=regime,
            stress_share=stress_share,
        )
        eigenvalue_frames.append(eigenvalues)
        summary_rows.append(summary)

    eigenvalues = pd.concat(eigenvalue_frames, ignore_index=True)
    summary = pd.DataFrame(summary_rows)
    comparison = build_comparison_row(universe, summary)
    return eigenvalues, summary, comparison


def build_comparison_row(universe: str, summary: pd.DataFrame) -> pd.DataFrame:
    """Compare calm and stress concentration metrics for one universe."""
    by_regime = summary.set_index("regime")
    calm = by_regime.loc["calm"]
    stress = by_regime.loc["stress"]

    pc1_change = float(stress["pc1_share"] - calm["pc1_share"])
    effective_bets_change = float(stress["effective_bets"] - calm["effective_bets"])
    more_concentrated = bool(pc1_change > 0 and effective_bets_change < 0)
    return pd.DataFrame(
        [
            {
                "universe": universe,
                "calm_pc1_share": float(calm["pc1_share"]),
                "stress_pc1_share": float(stress["pc1_share"]),
                "stress_minus_calm_pc1_share": pc1_change,
                "calm_effective_bets": float(calm["effective_bets"]),
                "stress_effective_bets": float(stress["effective_bets"]),
                "stress_minus_calm_effective_bets": effective_bets_change,
                "more_concentrated_in_stress": more_concentrated,
            }
        ]
    )


def write_pca_outputs(
    con,
    eigenvalues: pd.DataFrame,
    summary: pd.DataFrame,
    comparison: pd.DataFrame,
) -> None:
    """Insert PCA outputs into explicit-DDL tables. Schemas must already exist."""
    con.execute(
        f"""
        INSERT OR IGNORE INTO {EIGENVALUES_TABLE} (
            universe,
            regime,
            component,
            eigenvalue,
            explained_variance_share,
            cumulative_explained_variance_share
        )
        SELECT
            universe,
            regime,
            component,
            eigenvalue,
            explained_variance_share,
            cumulative_explained_variance_share
        FROM eigenvalues
        """
    )

    con.execute(
        f"""
        INSERT OR IGNORE INTO {SUMMARY_TABLE} (
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
        )
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
        FROM summary
        """
    )

    con.execute(
        f"""
        INSERT OR IGNORE INTO {COMPARISON_TABLE} (
            universe,
            calm_pc1_share,
            stress_pc1_share,
            stress_minus_calm_pc1_share,
            calm_effective_bets,
            stress_effective_bets,
            stress_minus_calm_effective_bets,
            more_concentrated_in_stress
        )
        SELECT
            universe,
            calm_pc1_share,
            stress_pc1_share,
            stress_minus_calm_pc1_share,
            calm_effective_bets,
            stress_effective_bets,
            stress_minus_calm_effective_bets,
            more_concentrated_in_stress
        FROM comparison
        """
    )
