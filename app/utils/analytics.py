"""Pure regime-conditional analytics for the dashboard.

Every formula the dashboard recomputes lives here exactly once. These functions
are pure (numpy / pandas only, no Streamlit, no IO) so they are unit-testable and
reused identically by every page. They operate on *exploratory* recomputations
from stored daily returns and the official Markov ``ms_stress`` label; they never
alter official pipeline outputs.

Correlation / PCA definitions mirror the research pipeline
(``src/analysis/regime_correlations.py`` and ``src/analysis/pca_concentration.py``):
PC1 share = lambda_1 / N, effective bets N_eff = (sum lambda)^2 / sum(lambda^2).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

CALM, STRESS = 0, 1
_TRADING_DAYS = 252


# --- Balanced sample ----------------------------------------------------------

def balanced_returns(returns: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Complete-case daily rows for ``columns`` plus the ``ms_stress`` label.

    Reproduces the paper's balanced window: rows where every requested asset is
    observed. Requires a ``date``, ``ms_stress`` column, and the return columns.
    """
    required = {"date", "ms_stress", *columns}
    missing = required - set(returns.columns)
    if missing:
        raise KeyError(f"returns is missing column(s): {', '.join(sorted(missing))}")
    frame = returns.loc[:, ["date", "ms_stress", *columns]].copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.dropna(subset=["ms_stress", *columns])
    frame["ms_stress"] = frame["ms_stress"].astype(int)
    return frame.sort_values("date", kind="stable").reset_index(drop=True)


def regime_slice(frame: pd.DataFrame, regime: int, columns: list[str]) -> pd.DataFrame:
    """Return the return columns for one regime (0 calm, 1 stress)."""
    return frame.loc[frame["ms_stress"] == regime, columns]


# --- Correlation --------------------------------------------------------------

def regime_correlation(frame: pd.DataFrame, columns: list[str], regime: int) -> pd.DataFrame:
    """Pearson correlation matrix for one regime, ordered like ``columns``."""
    sub = regime_slice(frame, regime, columns)
    if len(sub) < 3:
        raise ValueError(f"Need >=3 observations for a correlation matrix (got {len(sub)}).")
    return sub.corr(method="pearson").reindex(index=columns, columns=columns)


def average_pairwise_correlation(matrix: pd.DataFrame) -> float:
    """Mean of the unique off-diagonal correlations."""
    values = matrix.to_numpy(dtype=float)
    iu = np.triu_indices(values.shape[0], k=1)
    pairs = values[iu]
    pairs = pairs[np.isfinite(pairs)]
    return float(np.mean(pairs)) if pairs.size else float("nan")


# --- PCA concentration --------------------------------------------------------

def eigenvalues_from_correlation(matrix: pd.DataFrame) -> np.ndarray:
    """Sorted (descending), non-negative eigenvalues of a symmetric corr matrix."""
    values = matrix.to_numpy(dtype=float)
    values = (values + values.T) / 2.0
    eig = np.sort(np.linalg.eigvalsh(values))[::-1]
    eig[np.isclose(eig, 0.0, atol=1e-10)] = 0.0
    return np.clip(eig, 0.0, None)


def pc1_share(matrix: pd.DataFrame) -> float:
    """Share of total variance on the leading principal component (lambda_1 / N)."""
    eig = eigenvalues_from_correlation(matrix)
    total = float(eig.sum())
    if total <= 0:
        return float("nan")
    return float(eig[0] / total)


def effective_bets(matrix: pd.DataFrame) -> float:
    """Participation-ratio effective number of independent bets."""
    eig = eigenvalues_from_correlation(matrix)
    denom = float(np.sum(eig**2))
    if denom <= 0:
        return float("nan")
    return float((eig.sum() ** 2) / denom)


def explained_variance_shares(matrix: pd.DataFrame) -> np.ndarray:
    """Per-component explained-variance shares (eigenvalue / N), descending."""
    eig = eigenvalues_from_correlation(matrix)
    total = float(eig.sum())
    if total <= 0:
        return np.full(eig.shape, np.nan)
    return eig / total


# --- Portfolio diagnostics ----------------------------------------------------

def normalize_weights(weights: np.ndarray) -> np.ndarray:
    """Return weights scaled to sum to 1 (raises on non-finite or zero-sum)."""
    w = np.asarray(weights, dtype=float)
    if not np.isfinite(w).all():
        raise ValueError("weights contain non-finite values.")
    total = float(w.sum())
    if abs(total) < 1e-12:
        raise ValueError("weights sum to zero; cannot normalize.")
    return w / total


def covariance_matrix(frame: pd.DataFrame, columns: list[str], regime: int) -> pd.DataFrame:
    """Daily return covariance for one regime, ordered like ``columns``."""
    sub = regime_slice(frame, regime, columns)
    if len(sub) < 3:
        raise ValueError(f"Need >=3 observations for a covariance matrix (got {len(sub)}).")
    return sub.cov().reindex(index=columns, columns=columns)


def portfolio_volatility(weights: np.ndarray, cov: pd.DataFrame, *, annualize: bool = True) -> float:
    """Portfolio volatility sqrt(w' Sigma w); annualized from daily by sqrt(252)."""
    w = np.asarray(weights, dtype=float)
    sigma = cov.to_numpy(dtype=float)
    variance = float(w @ sigma @ w)
    variance = max(variance, 0.0)
    vol = np.sqrt(variance)
    return float(vol * np.sqrt(_TRADING_DAYS)) if annualize else float(vol)


@dataclass(frozen=True)
class RiskContribution:
    """Component risk contributions for one regime (daily volatility units)."""

    assets: list[str]
    marginal: np.ndarray       # MCR_i = (Sigma w)_i / sigma_p
    component: np.ndarray      # CCR_i = w_i * MCR_i   (sum -> sigma_p)
    portfolio_vol_daily: float

    @property
    def percent(self) -> np.ndarray:
        total = self.component.sum()
        return self.component / total if total > 0 else np.full_like(self.component, np.nan)


def risk_contributions(weights: np.ndarray, cov: pd.DataFrame) -> RiskContribution:
    """Euler risk decomposition: component contributions sum to portfolio volatility."""
    w = np.asarray(weights, dtype=float)
    sigma = cov.to_numpy(dtype=float)
    variance = max(float(w @ sigma @ w), 0.0)
    vol = np.sqrt(variance)
    if vol <= 0:
        n = len(w)
        return RiskContribution(list(cov.columns), np.full(n, np.nan), np.zeros(n), 0.0)
    marginal = (sigma @ w) / vol
    component = w * marginal
    return RiskContribution(list(cov.columns), marginal, component, float(vol))


@dataclass(frozen=True)
class VarianceDecomposition:
    """Portfolio variance split into own-variance and covariance terms."""

    portfolio_variance: float
    diagonal: float            # sum_i w_i^2 sigma_i^2
    off_diagonal: float        # 2 sum_{i<j} w_i w_j Cov(i,j)

    @property
    def diversification_share(self) -> float:
        """Share of variance coming from cross-asset covariance (can be negative)."""
        if abs(self.portfolio_variance) < 1e-18:
            return float("nan")
        return self.off_diagonal / self.portfolio_variance


def variance_decomposition(weights: np.ndarray, cov: pd.DataFrame) -> VarianceDecomposition:
    """Split w' Sigma w into diagonal (own-variance) and off-diagonal (covariance)."""
    w = np.asarray(weights, dtype=float)
    sigma = cov.to_numpy(dtype=float)
    total = float(w @ sigma @ w)
    diagonal = float(np.sum((w**2) * np.diag(sigma)))
    off_diagonal = total - diagonal
    return VarianceDecomposition(total, diagonal, off_diagonal)


def diversification_ratio(weights: np.ndarray, cov: pd.DataFrame) -> float:
    """Weighted average asset vol / portfolio vol (>=1; higher = more diversified)."""
    w = np.asarray(weights, dtype=float)
    sigma = cov.to_numpy(dtype=float)
    asset_vol = np.sqrt(np.clip(np.diag(sigma), 0.0, None))
    weighted_avg_vol = float(np.abs(w) @ asset_vol)
    port_vol = np.sqrt(max(float(w @ sigma @ w), 0.0))
    if port_vol <= 0:
        return float("nan")
    return float(weighted_avg_vol / port_vol)


# --- Stress-episode masks + statistics ----------------------------------------

def stress_episode_mask(frame: pd.DataFrame, year_from: int, year_to: int) -> pd.Series:
    """Boolean mask of official stress days within a calendar-year episode.

    ``frame`` must carry ``date`` and ``ms_stress``. Only ``ms_stress == 1`` rows
    inside ``[year_from, year_to]`` are selected, so the mask is guaranteed pure.
    """
    dates = pd.to_datetime(frame["date"])
    years = dates.dt.year
    return (frame["ms_stress"].astype(int) == STRESS) & years.between(year_from, year_to)


def episode_frame(
    balanced: pd.DataFrame, columns: list[str], *, era: tuple[int, int] | None,
) -> pd.DataFrame:
    """Return the stress-day rows for an episode (``era=None`` -> pooled stress)."""
    if era is None:
        mask = balanced["ms_stress"].astype(int) == STRESS
    else:
        mask = stress_episode_mask(balanced, era[0], era[1])
    return balanced.loc[mask, ["date", *columns]].reset_index(drop=True)


def episode_correlation(balanced: pd.DataFrame, columns: list[str], era: tuple[int, int] | None) -> pd.DataFrame:
    """Descriptive correlation matrix on official stress days for one episode."""
    sub = episode_frame(balanced, columns, era=era)
    if len(sub) < 3:
        raise ValueError(f"Episode has too few stress days for correlation (got {len(sub)}).")
    return sub[columns].corr(method="pearson").reindex(index=columns, columns=columns)


def episode_statistics(balanced: pd.DataFrame, columns: list[str], era: tuple[int, int] | None,
                       total_stress_days: int) -> dict[str, float]:
    """Descriptive episode summary: days, share, avg corr, PC1, Neff, SPY vol."""
    sub = episode_frame(balanced, columns, era=era)
    n = len(sub)
    stats: dict[str, float] = {
        "stress_days": n,
        "share_of_stress": (n / total_stress_days) if total_stress_days else float("nan"),
    }
    if n >= 3:
        cmat = sub[columns].corr(method="pearson").reindex(index=columns, columns=columns)
        stats["avg_correlation"] = average_pairwise_correlation(cmat)
        stats["pc1_share"] = pc1_share(cmat)
        stats["effective_bets"] = effective_bets(cmat)
        if "SPY" in columns:
            stats["spy_vol_annual"] = float(sub["SPY"].std(ddof=1) * np.sqrt(_TRADING_DAYS))
    else:
        stats.update(avg_correlation=float("nan"), pc1_share=float("nan"),
                     effective_bets=float("nan"), spy_vol_annual=float("nan"))
    return stats


def stress_spans(dates: pd.Series, flags: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Collapse a boolean stress flag into contiguous (start, end) date spans."""
    ds = pd.to_datetime(dates).reset_index(drop=True)
    fs = pd.Series(flags).fillna(False).astype(bool).reset_index(drop=True)
    spans: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    start = prev = None
    for d, f in zip(ds, fs):
        if f and start is None:
            start = d
        elif not f and start is not None:
            spans.append((start, prev))
            start = None
        prev = d
    if start is not None and prev is not None:
        spans.append((start, prev))
    return spans


def pair_correlation(sub: pd.DataFrame, asset_i: str, asset_j: str) -> float:
    """Correlation of one pair on a return sub-frame (nan if too few points)."""
    if asset_i not in sub.columns or asset_j not in sub.columns:
        return float("nan")
    two = sub[[asset_i, asset_j]].dropna()
    if len(two) < 3 or two[asset_i].std(ddof=1) == 0 or two[asset_j].std(ddof=1) == 0:
        return float("nan")
    return float(two[asset_i].corr(two[asset_j]))
