"""Cached dashboard data access (Streamlit layer over app/data Parquet files).

Official pages read precomputed Parquet exports; exploratory recomputation reads
the stored daily returns + official ``ms_stress`` label. Nothing here writes back
to the pipeline. All loaders are cached with ``st.cache_data``.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.utils.analytics import balanced_returns
from app.utils.constants import ETF_ASSETS
from app.utils.data import load_parquet


def _safe(filename: str) -> pd.DataFrame:
    try:
        return load_parquet(filename)
    except (ImportError, OSError, ValueError):
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_returns() -> pd.DataFrame:
    """Stored daily ETF returns with the official monthly Markov ``ms_stress`` label."""
    frame = _safe("returns.parquet")
    if frame.empty:
        return frame
    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    for col in ETF_ASSETS:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    if "ms_stress" in frame.columns:
        frame["ms_stress"] = pd.to_numeric(frame["ms_stress"], errors="coerce")
    return frame.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def available_assets() -> list[str]:
    """Return columns of the final universe actually present in the return panel."""
    frame = load_returns()
    return [asset for asset in ETF_ASSETS if asset in frame.columns]


@st.cache_data(show_spinner=False)
def load_balanced(columns: tuple[str, ...]) -> pd.DataFrame:
    """Cached complete-case balanced panel for a set of columns (tuple = hashable key)."""
    frame = load_returns()
    if frame.empty:
        return frame
    return balanced_returns(frame, list(columns))


@st.cache_data(show_spinner=False)
def total_stress_days() -> int:
    """Official Markov stress-day count on the full 14-asset balanced window."""
    bal = load_balanced(tuple(ETF_ASSETS))
    if bal.empty:
        return 0
    return int((bal["ms_stress"] == 1).sum())


# --- Precomputed official exports (thin cached passthroughs) ------------------

@st.cache_data(show_spinner=False)
def load_corr_pairs() -> pd.DataFrame:
    frame = _safe("corr_pairs.parquet")
    if frame.empty:
        return frame
    frame = frame.copy()
    for col in ["universe", "method", "regime", "asset_i", "asset_j"]:
        frame[col] = frame[col].astype(str)
    frame["correlation"] = pd.to_numeric(frame["correlation"], errors="coerce")
    return frame


@st.cache_data(show_spinner=False)
def load_pca_summary() -> pd.DataFrame:
    return _safe("pca_regime_concentration_summary.parquet")


@st.cache_data(show_spinner=False)
def load_pca_eigenvalues() -> pd.DataFrame:
    return _safe("pca_regime_concentration_eigenvalues.parquet")


@st.cache_data(show_spinner=False)
def load_pca_comparison() -> pd.DataFrame:
    return _safe("pca_regime_concentration_comparison.parquet")


@st.cache_data(show_spinner=False)
def load_fr_pairs() -> pd.DataFrame:
    frame = _safe("forbes_rigobon_adjusted_pairs.parquet")
    if frame.empty:
        return frame
    frame = frame.copy()
    for col in ["universe", "fr_method", "source_asset", "asset_i", "asset_j", "interpretation"]:
        if col in frame.columns:
            frame[col] = frame[col].astype(str)
    return frame


@st.cache_data(show_spinner=False)
def load_fr_summary() -> pd.DataFrame:
    return _safe("forbes_rigobon_adjusted_summary.parquet")


@st.cache_data(show_spinner=False)
def load_fr_variance_ratios() -> pd.DataFrame:
    return _safe("forbes_rigobon_variance_ratios.parquet")


@st.cache_data(show_spinner=False)
def load_bootstrap_pairs() -> pd.DataFrame:
    frame = _safe("bootstrap_pair_results.parquet")
    if frame.empty:
        return frame
    frame = frame.copy()
    for col in ["universe", "asset_i", "asset_j", "direction"]:
        if col in frame.columns:
            frame[col] = frame[col].astype(str)
    return frame


@st.cache_data(show_spinner=False)
def load_rolling_pairs() -> pd.DataFrame:
    """Optional precomputed 126-day rolling correlations for headline pairs."""
    frame = _safe("rolling_pair_correlations.parquet")
    if frame.empty:
        return frame
    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["rolling_correlation"] = pd.to_numeric(frame["rolling_correlation"], errors="coerce")
    return frame


@st.cache_data(show_spinner=False)
def load_rolling_absorption() -> pd.DataFrame:
    """Optional precomputed 126-day rolling PCA concentration (absorption ratio)."""
    frame = _safe("rolling_absorption_ratio.parquet")
    if frame.empty:
        return frame
    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    for col in ["pc1_share", "effective_bets"]:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


@st.cache_data(show_spinner=False)
def official_stress_spans() -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Contiguous official Markov stress spans from the stored daily label."""
    from app.utils.analytics import stress_spans

    frame = load_returns()
    if frame.empty or "ms_stress" not in frame.columns:
        return []
    return stress_spans(frame["date"], frame["ms_stress"] == 1)


@st.cache_data(show_spinner=False)
def load_episode_broad() -> pd.DataFrame:
    """Precomputed broad-era stress-episode correlations (validation reference)."""
    return _safe("stress_episode_all_pairs_broad.parquet")


@st.cache_data(show_spinner=False)
def load_episode_ranking() -> pd.DataFrame:
    return _safe("stress_episode_pair_heterogeneity_ranking.parquet")
