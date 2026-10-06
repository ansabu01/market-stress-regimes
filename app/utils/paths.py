"""Project-relative paths for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
APP_DATA_DIR = APP_DIR / "data"
DB_PATH = PROJECT_ROOT / "data" / "lsr.duckdb"

EXPECTED_PARQUET_FILES = {
    "regime_timeseries.parquet": "Regime timeline",
    "returns.parquet": "Daily returns",
    "corr_pairs.parquet": "Correlation pairs",
    "pca_regime_concentration_summary.parquet": "PCA summary",
    "pca_regime_concentration_eigenvalues.parquet": "PCA eigenvalues",
    "pca_regime_concentration_comparison.parquet": "PCA comparison",
    "forbes_rigobon_adjusted_pairs.parquet": "Forbes-Rigobon pairs",
    "forbes_rigobon_adjusted_summary.parquet": "Forbes-Rigobon summary",
    "forbes_rigobon_variance_ratios.parquet": "Forbes-Rigobon variances",
    "bootstrap_pair_results.parquet": "Bootstrap pair inference",
    "stress_episode_all_pairs_broad.parquet": "Broad stress episodes",
    "stress_episode_all_pairs_granular.parquet": "Granular stress episodes",
    "stress_episode_pair_heterogeneity_ranking.parquet": "Episode heterogeneity",
    "markov_chain_transition_matrix.parquet": "Markov transition matrix",
}

OPTIONAL_PARQUET_FILES = {
    "rolling_pair_correlations.parquet": "Rolling pair correlations",
    "rolling_absorption_ratio.parquet": "Rolling absorption ratio",
}


def repo_relative(path: Path) -> str:
    """Return a stable project-relative path string for display."""
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()
