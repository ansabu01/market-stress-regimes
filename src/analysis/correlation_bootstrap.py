"""Moving-block bootstrap inference for regime-conditional correlations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import norm


@dataclass(frozen=True)
class CorrelationBootstrapResult:
    """Pair-level results and bootstrap draws for one return universe."""

    pair_results: pd.DataFrame
    universe_summary: pd.DataFrame
    calm_draws: np.ndarray
    stress_draws: np.ndarray
    delta_draws: np.ndarray


def circular_block_indices(
    n_observations: int,
    block_length: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Draw ``n_observations`` indices using a circular moving-block bootstrap."""
    if n_observations < 2:
        raise ValueError("Need at least two observations for block resampling.")
    if not 1 <= block_length <= n_observations:
        raise ValueError("block_length must be between 1 and n_observations.")

    n_blocks = int(np.ceil(n_observations / block_length))
    starts = rng.integers(0, n_observations, size=n_blocks)
    offsets = np.arange(block_length)
    indices = (starts[:, None] + offsets[None, :]) % n_observations
    return indices.ravel()[:n_observations]


def benjamini_hochberg(p_values: np.ndarray | pd.Series) -> np.ndarray:
    """Return Benjamini-Hochberg adjusted p-values."""
    values = np.asarray(p_values, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("p_values must be a finite one-dimensional array.")
    if ((values < 0) | (values > 1)).any():
        raise ValueError("p_values must lie between zero and one.")

    order = np.argsort(values)
    ranked = values[order]
    adjusted = ranked * len(values) / np.arange(1, len(values) + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]

    result = np.empty_like(adjusted)
    result[order] = np.clip(adjusted, 0.0, 1.0)
    return result


def fisher_z_difference_test(
    corr_calm: np.ndarray,
    corr_stress: np.ndarray,
    n_calm: int,
    n_stress: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Compare independent correlations using the classical Fisher-z approximation."""
    if n_calm <= 3 or n_stress <= 3:
        raise ValueError("Fisher-z comparison needs more than three observations per regime.")

    calm = np.clip(np.asarray(corr_calm, dtype=float), -1 + 1e-12, 1 - 1e-12)
    stress = np.clip(np.asarray(corr_stress, dtype=float), -1 + 1e-12, 1 - 1e-12)
    standard_error = np.sqrt(1 / (n_calm - 3) + 1 / (n_stress - 3))
    z_stat = (np.arctanh(stress) - np.arctanh(calm)) / standard_error
    p_value = 2 * norm.sf(np.abs(z_stat))
    return z_stat, p_value


def _validate_inputs(
    data: pd.DataFrame,
    return_columns: list[str],
    regime_col: str,
    n_bootstrap: int,
    block_length: int,
    confidence_level: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if len(return_columns) < 2:
        raise ValueError("Need at least two return columns.")
    if len(set(return_columns)) != len(return_columns):
        raise ValueError("return_columns contains duplicates.")

    required = {regime_col, *return_columns}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if n_bootstrap < 100:
        raise ValueError("n_bootstrap must be at least 100.")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie between zero and one.")

    regimes = data[regime_col]
    if regimes.isna().any() or not set(regimes.unique()).issubset({0, 1}):
        raise ValueError(f"{regime_col} must contain only non-missing 0/1 values.")

    values = data[return_columns].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Return data must be complete and finite.")

    regime_values = regimes.to_numpy(dtype=int)
    if not 1 <= block_length <= len(values):
        raise ValueError("block_length must be between 1 and the number of observations.")

    calm = values[regime_values == 0]
    stress = values[regime_values == 1]
    if min(len(calm), len(stress)) <= 3:
        raise ValueError("Each regime needs more than three observations.")
    if (np.std(calm, axis=0, ddof=1) == 0).any():
        raise ValueError("At least one calm return series has zero variance.")
    if (np.std(stress, axis=0, ddof=1) == 0).any():
        raise ValueError("At least one stress return series has zero variance.")
    return values, regime_values, calm, stress


def _correlation_pairs(
    values: np.ndarray,
    triangle: tuple[np.ndarray, np.ndarray],
) -> np.ndarray:
    matrix = np.corrcoef(values, rowvar=False)
    pairs = matrix[triangle]
    if not np.isfinite(pairs).all():
        raise RuntimeError("A bootstrap sample produced a non-finite correlation.")
    return pairs


def _two_sided_centered_bootstrap_p(
    draws: np.ndarray,
    observed: np.ndarray,
) -> np.ndarray:
    """Return centered two-sided bootstrap p-values for a zero null.

    The centered bootstrap errors approximate the statistic's distribution
    around the null. The p-value is the share whose absolute error is at least
    as large as the absolute observed statistic, with a finite-sample
    continuity correction.
    """
    n_bootstrap = draws.shape[0]
    observed_values = np.asarray(observed, dtype=float)
    centered_errors = draws - observed_values
    exceedances = np.sum(
        np.abs(centered_errors) >= np.abs(observed_values),
        axis=0,
    )
    return (exceedances + 1) / (n_bootstrap + 1)


def _ordered_by_date(data: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Validate dates and return a stable chronological copy."""
    if date_col not in data.columns:
        raise ValueError(f"Missing required date column: {date_col}")

    ordered = data.copy()
    ordered[date_col] = pd.to_datetime(ordered[date_col])
    if ordered[date_col].isna().any():
        raise ValueError(f"{date_col} must not contain missing dates.")
    if ordered[date_col].duplicated().any():
        raise ValueError(f"{date_col} must contain unique dates.")
    return ordered.sort_values(date_col, kind="stable").reset_index(drop=True)


def bootstrap_correlation_changes(
    data: pd.DataFrame,
    return_columns: list[str],
    *,
    universe: str,
    regime_col: str = "ms_stress",
    date_col: str = "date",
    n_bootstrap: int = 2_000,
    block_length: int = 21,
    confidence_level: float = 0.95,
    seed: int = 20250624,
) -> CorrelationBootstrapResult:
    """Bootstrap calm, stress, and stress-minus-calm pair correlations.

    Complete cross-sectional rows and their regime labels are sampled together
    in chronological circular blocks. Correlations are computed after each
    resample is split by regime, so blocks preserve real temporal adjacency and
    bootstrap regime counts are allowed to vary.
    """
    ordered = _ordered_by_date(data, date_col)
    values, regimes, calm, stress = _validate_inputs(
        ordered,
        return_columns,
        regime_col,
        n_bootstrap,
        block_length,
        confidence_level,
    )
    n_assets = len(return_columns)
    triangle = np.triu_indices(n_assets, k=1)
    n_pairs = len(triangle[0])
    rng = np.random.default_rng(seed)

    corr_calm = _correlation_pairs(calm, triangle)
    corr_stress = _correlation_pairs(stress, triangle)
    observed_delta = corr_stress - corr_calm

    calm_draws = np.empty((n_bootstrap, n_pairs), dtype=float)
    stress_draws = np.empty((n_bootstrap, n_pairs), dtype=float)
    calm_counts = np.empty(n_bootstrap, dtype=int)
    stress_counts = np.empty(n_bootstrap, dtype=int)
    for draw in range(n_bootstrap):
        for attempt in range(1_000):
            indices = circular_block_indices(len(values), block_length, rng)
            sampled_values = values[indices]
            sampled_regimes = regimes[indices]
            sampled_calm = sampled_values[sampled_regimes == 0]
            sampled_stress = sampled_values[sampled_regimes == 1]

            valid_counts = min(len(sampled_calm), len(sampled_stress)) > 3
            valid_variances = valid_counts and not (
                (np.std(sampled_calm, axis=0, ddof=1) == 0).any()
                or (np.std(sampled_stress, axis=0, ddof=1) == 0).any()
            )
            if valid_variances:
                break
        else:
            raise RuntimeError(
                "Could not draw a valid chronological bootstrap sample after 1,000 attempts."
            )

        calm_counts[draw] = len(sampled_calm)
        stress_counts[draw] = len(sampled_stress)
        calm_draws[draw] = _correlation_pairs(sampled_calm, triangle)
        stress_draws[draw] = _correlation_pairs(sampled_stress, triangle)
    delta_draws = stress_draws - calm_draws

    alpha = 1 - confidence_level
    ci_low, ci_high = np.quantile(delta_draws, [alpha / 2, 1 - alpha / 2], axis=0)
    p_bootstrap = _two_sided_centered_bootstrap_p(delta_draws, observed_delta)
    q_value = benjamini_hochberg(p_bootstrap)
    fisher_z, p_fisher = fisher_z_difference_test(
        corr_calm,
        corr_stress,
        len(calm),
        len(stress),
    )

    pair_results = pd.DataFrame(
        {
            "universe": universe,
            "asset_i": np.asarray(return_columns)[triangle[0]],
            "asset_j": np.asarray(return_columns)[triangle[1]],
            "corr_calm": corr_calm,
            "corr_stress": corr_stress,
            "delta_corr": observed_delta,
            "bootstrap_se": np.std(delta_draws, axis=0, ddof=1),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "p_boot_two_sided": p_bootstrap,
            "q_value_bh": q_value,
            "fisher_z_stat": fisher_z,
            "p_fisher_z": p_fisher,
        }
    )
    pair_results["significant_95"] = (pair_results["ci_low"] > 0) | (
        pair_results["ci_high"] < 0
    )
    pair_results["significant_fdr_05"] = pair_results["q_value_bh"] < 0.05
    pair_results["direction"] = np.select(
        [pair_results["ci_low"] > 0, pair_results["ci_high"] < 0],
        ["increase", "decrease"],
        default="inconclusive",
    )
    average_draws = delta_draws.mean(axis=1)
    median_draws = np.median(delta_draws, axis=1)
    avg_ci = np.quantile(average_draws, [alpha / 2, 1 - alpha / 2])
    median_ci = np.quantile(median_draws, [alpha / 2, 1 - alpha / 2])
    observed_average = float(np.mean(observed_delta))
    observed_median = float(np.median(observed_delta))
    avg_p = float(
        _two_sided_centered_bootstrap_p(
            average_draws[:, None],
            np.array([observed_average]),
        )[0]
    )
    median_p = float(
        _two_sided_centered_bootstrap_p(
            median_draws[:, None],
            np.array([observed_median]),
        )[0]
    )

    universe_summary = pd.DataFrame(
        [
            {
                "universe": universe,
                "n_assets": n_assets,
                "n_pairs": n_pairs,
                "n_calm_days": len(calm),
                "n_stress_days": len(stress),
                "bootstrap_calm_days_min": int(calm_counts.min()),
                "bootstrap_calm_days_max": int(calm_counts.max()),
                "bootstrap_stress_days_min": int(stress_counts.min()),
                "bootstrap_stress_days_max": int(stress_counts.max()),
                "n_bootstrap": n_bootstrap,
                "block_length": block_length,
                "confidence_level": confidence_level,
                "avg_delta_corr": observed_average,
                "avg_ci_low": float(avg_ci[0]),
                "avg_ci_high": float(avg_ci[1]),
                "avg_p_boot_two_sided": avg_p,
                "median_delta_corr": observed_median,
                "median_ci_low": float(median_ci[0]),
                "median_ci_high": float(median_ci[1]),
                "median_p_boot_two_sided": median_p,
                "significant_increases_95": int((pair_results["ci_low"] > 0).sum()),
                "significant_decreases_95": int((pair_results["ci_high"] < 0).sum()),
                "significant_pairs_fdr_05": int(pair_results["significant_fdr_05"].sum()),
            }
        ]
    )
    return CorrelationBootstrapResult(
        pair_results=pair_results,
        universe_summary=universe_summary,
        calm_draws=calm_draws,
        stress_draws=stress_draws,
        delta_draws=delta_draws,
    )
