from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse import linalg as sparse_linalg

"""
Simple L1 trend filtering.

We estimate a clean trend beta from a noisy time series y by solving:

    0.5 * ||y - beta||_2^2 + lam * ||D beta||_1

The first term keeps beta close to the data.
The second term penalizes changes in the trend.

The matrix D is a finite-difference matrix:

    degree = 0 -> D is first differences, so beta is piecewise constant.
    degree = 1 -> D is second differences, so beta is piecewise linear.

For our regime work, degree=1 is the useful default: it smooths noise while
keeping important turning points.
"""


@dataclass(frozen=True)
class TrendFilterResult:
    """Small diagnostic object returned by trend_filter."""

    trend: np.ndarray
    converged: bool
    iterations: int
    primal_residual: float
    dual_residual: float


def make_difference_matrix(n_obs: int, order: int) -> sparse.csc_matrix:
    """
    Build the finite-difference matrix D.

    Example with order=1:
        D beta = [beta_1 - beta_0, beta_2 - beta_1, ...]

    Example with order=2:
        D beta = [beta_2 - 2 beta_1 + beta_0, ...]
    """
    if order < 1:
        raise ValueError("order must be at least 1")
    if n_obs <= order:
        raise ValueError("n_obs must be greater than order")

    difference = sparse.eye(n_obs, format="csc", dtype=float)
    for _ in range(order):
        difference = difference[1:] - difference[:-1]

    return difference.tocsc()


def soft_threshold(values: np.ndarray, threshold: float) -> np.ndarray:
    """
    Shrink small values to zero.

    This is the L1 part of the algorithm. It is what makes many trend changes
    exactly zero, creating simple piecewise trends instead of noisy wiggles.
    """
    return np.sign(values) * np.maximum(np.abs(values) - threshold, 0.0)


def trend_filter(
    y: np.ndarray,
    lam: float,
    degree: int = 1,
    rho: float = 1.0,
    max_iter: int = 2_000,
    tol: float = 1e-3,
) -> TrendFilterResult:
    """
    Estimate the smooth trend for a one-dimensional array.

    Parameters
    ----------
    y:
        Noisy observed data.
    lam:
        Smoothness parameter. Larger values produce smoother trends.
    degree:
        0 = piecewise constant, 1 = piecewise linear.
    rho:
        ADMM tuning parameter. Usually leave at 1.0.
    max_iter:
        Maximum number of ADMM iterations.
    tol:
        Convergence tolerance.

    Returns
    -------
    TrendFilterResult
        Contains the estimated trend and a few convergence diagnostics.
    """
    y = np.asarray(y, dtype=float)

    if y.ndim != 1:
        raise ValueError("y must be one-dimensional")
    if not np.isfinite(y).all():
        raise ValueError("y must not contain NaN or infinite values")
    if lam < 0:
        raise ValueError("lam must be non-negative")
    if degree < 0:
        raise ValueError("degree must be non-negative")

    n_obs = y.size
    difference_order = degree + 1

    if lam == 0 or n_obs <= difference_order:
        return TrendFilterResult(
            trend=y.copy(),
            converged=True,
            iterations=0,
            primal_residual=0.0,
            dual_residual=0.0,
        )

    # Step 1: Build D from the formula ||D beta||_1.
    difference = make_difference_matrix(n_obs, difference_order)

    # Step 2: Pre-factorize the linear system used in every ADMM iteration.
    # This is the expensive part, so we do it once.
    identity = sparse.eye(n_obs, format="csc")
    system_matrix = identity + rho * (difference.T @ difference)
    solve_beta_step = sparse_linalg.factorized(system_matrix.tocsc())

    # ADMM variables:
    # beta is the smooth trend we want.
    # z is the sparse version of D beta.
    # u is the dual variable that keeps z and D beta consistent.
    beta = y.copy()
    z = np.zeros(difference.shape[0])
    u = np.zeros_like(z)

    primal_residual = np.inf
    dual_residual = np.inf
    converged = False

    for iteration in range(1, max_iter + 1):
        z_previous = z.copy()

        # A. Fit beta close to y, while respecting the current smoothness target.
        right_hand_side = y + rho * (difference.T @ (z - u))
        beta = solve_beta_step(right_hand_side)

        # B. Compute the current trend changes.
        raw_trend_changes = difference @ beta

        # C. Apply L1 shrinkage. Small changes become exactly zero.
        z = soft_threshold(raw_trend_changes + u, lam / rho)

        # D. Update the dual variable.
        u = u + raw_trend_changes - z

        # E. Stop when beta and z agree closely enough.
        # The tolerances scale with the series length, so long daily series do
        # not get judged by an unrealistically tiny absolute error.
        primal_residual = float(np.linalg.norm(raw_trend_changes - z))
        dual_residual = float(np.linalg.norm(rho * (difference.T @ (z - z_previous))))

        primal_tolerance = np.sqrt(z.size) * tol + tol * max(
            np.linalg.norm(raw_trend_changes),
            np.linalg.norm(z),
        )
        dual_tolerance = np.sqrt(n_obs) * tol + tol * np.linalg.norm(rho * (difference.T @ u))

        if primal_residual <= primal_tolerance and dual_residual <= dual_tolerance:
            converged = True
            break

    return TrendFilterResult(
        trend=beta,
        converged=converged,
        iterations=iteration,
        primal_residual=primal_residual,
        dual_residual=dual_residual,
    )


def trend_filter_series(
    series: pd.Series,
    lam: float,
    degree: int = 1,
    standardize: bool = True,
    **kwargs: object,
) -> pd.Series:
    """
    Apply trend filtering to a pandas Series and keep the original date index.

    This is the function you will usually call from notebooks or scripts.

    Example:
        vix_trend = trend_filter_series(vix["close"], lam=45, degree=1)
    """
    clean = series.dropna().astype(float)
    output_name = f"{series.name}_trend" if series.name else "trend"

    if clean.empty:
        return pd.Series(index=series.index, dtype=float, name=output_name)

    values = clean.to_numpy()

    if standardize:
        mean = values.mean()
        std = values.std(ddof=0)
        fit_values = (values - mean) / std if std > 0 else values
    else:
        mean = 0.0
        std = 1.0
        fit_values = values

    result = trend_filter(fit_values, lam=lam, degree=degree, **kwargs)
    trend_values = result.trend * std + mean if standardize and std > 0 else result.trend

    trend = pd.Series(trend_values, index=clean.index, name=output_name)
    return trend.reindex(series.index)


def stabilize_stress_flags(
    flags: pd.Series,
    min_stress_days: int,
    min_calm_days: int,
) -> pd.Series:
    """
    Make the stress regime more stable.

    - Short calm gaps inside stress episodes are filled.
    - Short stress blips are removed.
    """
    stable = flags.fillna(0).astype(bool).to_numpy(copy=True)

    def runs(values: np.ndarray) -> list[tuple[int, int, bool]]:
        out = []
        start = 0
        current = bool(values[0])

        for index, value in enumerate(values[1:], start=1):
            value = bool(value)
            if value != current:
                out.append((start, index - 1, current))
                start = index
                current = value

        out.append((start, len(values) - 1, current))
        return out

    if stable.size == 0:
        return flags.astype(int)

    for start, end, is_stress in runs(stable):
        length = end - start + 1
        is_internal_gap = start > 0 and end < stable.size - 1
        if not is_stress and is_internal_gap and length < min_calm_days:
            stable[start : end + 1] = True

    for start, end, is_stress in runs(stable):
        length = end - start + 1
        if is_stress and length < min_stress_days:
            stable[start : end + 1] = False

    return pd.Series(stable.astype(int), index=flags.index, name=flags.name)


def assign_stress_episode_ids(stable_flags: pd.Series) -> pd.Series:
    """
    Number each contiguous stress run 1, 2, 3, ...

    Values outside a stress run are NaN so the column can map to a nullable
    INTEGER on the SQL side.
    """
    flags = stable_flags.fillna(0).astype(int).to_numpy()
    episode = np.full(flags.shape, np.nan, dtype=float)
    current_id = 0
    in_episode = False

    for index, value in enumerate(flags):
        if value == 1:
            if not in_episode:
                current_id += 1
                in_episode = True
            episode[index] = current_id
        else:
            in_episode = False

    return pd.Series(episode, index=stable_flags.index, name="episode_id")


def build_trend_filter_regime_table(
    spy_close: pd.Series,
    vix_close: pd.Series,
    *,
    vix_lam: float,
    drawdown_lam: float,
    trend_degree: int,
    standardize: bool,
    vix_quantile: float,
    vix_window: int,
    drawdown_threshold: float,
    min_stress_days: int,
    min_calm_days: int,
) -> pd.DataFrame:
    """
    Build the trend-filter robustness regime table from raw SPY and VIX series.

    Returns a DataFrame with columns matching `trend_filter_regime_daily`:
        date, spy_close_adj, vix_close_adj, spy_drawdown_raw, spy_drawdown_trend,
        vix_log, vix_trend, vix_trend_q75_252_lag, stress_trend_raw,
        stress_trend_stable, episode_id

    Rows where the trailing VIX quantile is undefined (the first `vix_window`
    observations) are dropped so the SQL CHECK constraints on the stress flags
    are satisfied.
    """
    spy = spy_close.astype(float).rename("spy_close_adj")
    vix = vix_close.astype(float).rename("vix_close_adj")
    spy, vix = spy.align(vix, join="inner")
    spy = spy.sort_index()
    vix = vix.sort_index()

    spy_rollmax = spy.rolling(window=vix_window, min_periods=1).max()
    spy_drawdown_raw = ((spy_rollmax - spy) / spy_rollmax).rename("spy_drawdown_raw")

    vix_log = np.log(vix).rename("vix_log")
    log_vix_trend = trend_filter_series(
        vix_log, lam=vix_lam, degree=trend_degree, standardize=standardize
    )
    vix_trend = np.exp(log_vix_trend).rename("vix_trend")

    spy_drawdown_trend = trend_filter_series(
        spy_drawdown_raw,
        lam=drawdown_lam,
        degree=trend_degree,
        standardize=standardize,
    ).clip(lower=0).rename("spy_drawdown_trend")

    vix_trend_q75_252_lag = (
        vix_trend
        .shift(1)
        .rolling(window=vix_window, min_periods=vix_window)
        .quantile(vix_quantile)
        .rename("vix_trend_q75_252_lag")
    )

    stress_trend_raw = (
        (vix_trend > vix_trend_q75_252_lag) & (spy_drawdown_trend > drawdown_threshold)
    ).astype(int).rename("stress_trend_raw")

    stress_trend_stable = stabilize_stress_flags(
        stress_trend_raw,
        min_stress_days=min_stress_days,
        min_calm_days=min_calm_days,
    ).rename("stress_trend_stable")

    episode_id = assign_stress_episode_ids(stress_trend_stable)

    table = pd.concat(
        [
            spy,
            vix,
            spy_drawdown_raw,
            spy_drawdown_trend,
            vix_log,
            vix_trend,
            vix_trend_q75_252_lag,
            stress_trend_raw,
            stress_trend_stable,
            episode_id,
        ],
        axis=1,
    )

    table = table.dropna(subset=["vix_trend_q75_252_lag"]).copy()
    table.index.name = "date"
    table = table.reset_index()
    table["date"] = pd.to_datetime(table["date"]).dt.date
    return table[
        [
            "date",
            "spy_close_adj",
            "vix_close_adj",
            "spy_drawdown_raw",
            "spy_drawdown_trend",
            "vix_log",
            "vix_trend",
            "vix_trend_q75_252_lag",
            "stress_trend_raw",
            "stress_trend_stable",
            "episode_id",
        ]
    ]
