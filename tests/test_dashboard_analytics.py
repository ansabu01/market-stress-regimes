"""Tests for the dashboard's pure analytics + episode recomputation.

These validate the diagnostic identities the Portfolio X-Ray and Stress Anatomy
pages rely on, and confirm that live episode recomputation reproduces the stored
report table. Run: ``python -m pytest tests/test_dashboard_analytics.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.utils import analytics as A  # noqa: E402
from app.utils.constants import BROAD_ERAS, ETF_ASSETS, PANEL_A, PANEL_B, UNIVERSES  # noqa: E402

DATA = PROJECT_ROOT / "app" / "data"
RETURNS = DATA / "returns.parquet"
EPISODE_BROAD = DATA / "stress_episode_all_pairs_broad.parquet"
PCA_SUMMARY = DATA / "pca_regime_concentration_summary.parquet"

pytestmark = pytest.mark.skipif(not RETURNS.exists(), reason="dashboard exports not built")


@pytest.fixture(scope="module")
def returns() -> pd.DataFrame:
    return pd.read_parquet(RETURNS)


@pytest.fixture(scope="module")
def balanced(returns) -> pd.DataFrame:
    return A.balanced_returns(returns, ETF_ASSETS)


# --- Balanced sample ----------------------------------------------------------

def test_balanced_window(balanced):
    assert len(balanced) == 4711
    assert int((balanced["ms_stress"] == 0).sum()) == 2443
    assert int((balanced["ms_stress"] == 1).sum()) == 2268
    assert set(balanced["ms_stress"].unique()) <= {0, 1}


# --- PC1 / Neff identities ----------------------------------------------------

@pytest.mark.parametrize("cols", [PANEL_A, PANEL_B, ETF_ASSETS])
@pytest.mark.parametrize("regime", [A.CALM, A.STRESS])
def test_pc1_in_range(balanced, cols, regime):
    cmat = A.regime_correlation(balanced, cols, regime)
    pc1 = A.pc1_share(cmat)
    assert 1.0 / len(cols) - 1e-9 <= pc1 <= 1.0 + 1e-9


@pytest.mark.parametrize("cols", [PANEL_A, PANEL_B, ETF_ASSETS])
@pytest.mark.parametrize("regime", [A.CALM, A.STRESS])
def test_neff_bounds(balanced, cols, regime):
    cmat = A.regime_correlation(balanced, cols, regime)
    neff = A.effective_bets(cmat)
    assert 1.0 - 1e-6 <= neff <= len(cols) + 1e-6


def test_pc1_neff_match_official(balanced):
    official = pd.read_parquet(PCA_SUMMARY)
    for universe, cols in UNIVERSES.items():
        cmat = A.regime_correlation(balanced, cols, A.STRESS)
        row = official[(official["universe"] == universe) & (official["regime"] == "stress")].iloc[0]
        assert A.pc1_share(cmat) == pytest.approx(float(row["pc1_share"]), abs=1e-6)
        assert A.effective_bets(cmat) == pytest.approx(float(row["effective_bets"]), abs=1e-6)


# --- Correlation bounds -------------------------------------------------------

@pytest.mark.parametrize("cols", [PANEL_A, ETF_ASSETS])
def test_correlations_within_bounds(balanced, cols):
    for era in [None, (2007, 2019), (2020, 2021), (2022, 2023)]:
        cmat = A.episode_correlation(balanced, cols, era)
        vals = cmat.to_numpy()
        assert np.nanmax(vals) <= 1.0 + 1e-9
        assert np.nanmin(vals) >= -1.0 - 1e-9


# --- Portfolio identities -----------------------------------------------------

def _weights(n, seed=0):
    rng = np.random.default_rng(seed)
    return A.normalize_weights(rng.uniform(0.05, 1.0, n))


@pytest.mark.parametrize("cols", [PANEL_A, ETF_ASSETS, ["SPY", "TLT", "GLD"]])
def test_portfolio_variance_matches_quadratic_form(balanced, cols):
    w = _weights(len(cols))
    cov = A.covariance_matrix(balanced, cols, A.STRESS)
    expected = float(w @ cov.to_numpy() @ w)
    vol_daily = A.portfolio_volatility(w, cov, annualize=False)
    assert vol_daily ** 2 == pytest.approx(expected, rel=1e-10)


@pytest.mark.parametrize("cols", [PANEL_A, ETF_ASSETS])
@pytest.mark.parametrize("regime", [A.CALM, A.STRESS])
def test_risk_contributions_sum_to_volatility(balanced, cols, regime):
    w = _weights(len(cols), seed=1)
    cov = A.covariance_matrix(balanced, cols, regime)
    rc = A.risk_contributions(w, cov)
    assert rc.component.sum() == pytest.approx(rc.portfolio_vol_daily, rel=1e-10)
    assert rc.portfolio_vol_daily == pytest.approx(A.portfolio_volatility(w, cov, annualize=False), rel=1e-10)


@pytest.mark.parametrize("cols", [PANEL_A, ETF_ASSETS])
@pytest.mark.parametrize("regime", [A.CALM, A.STRESS])
def test_variance_decomposition_identity(balanced, cols, regime):
    w = _weights(len(cols), seed=2)
    cov = A.covariance_matrix(balanced, cols, regime)
    vd = A.variance_decomposition(w, cov)
    assert vd.portfolio_variance == pytest.approx(vd.diagonal + vd.off_diagonal, abs=1e-14)
    assert vd.portfolio_variance == pytest.approx(float(w @ cov.to_numpy() @ w), rel=1e-10)


# --- Weights ------------------------------------------------------------------

def test_equal_weights_sum_to_one():
    for n in (2, 5, 14):
        assert np.isclose(np.full(n, 1.0 / n).sum(), 1.0)


def test_custom_weights_normalize():
    w = A.normalize_weights(np.array([10.0, 30.0, 60.0]))
    assert w.sum() == pytest.approx(1.0)
    assert np.allclose(w, [0.1, 0.3, 0.6])


def test_zero_sum_weights_raise():
    with pytest.raises(ValueError):
        A.normalize_weights(np.zeros(3))


# --- Episode masks ------------------------------------------------------------

@pytest.mark.parametrize("era", [(2007, 2019), (2020, 2021), (2022, 2023)])
def test_episode_mask_is_pure_stress(balanced, era):
    mask = A.stress_episode_mask(balanced, *era)
    assert (balanced.loc[mask, "ms_stress"] == 1).all()
    years = pd.to_datetime(balanced.loc[mask, "date"]).dt.year
    assert years.between(era[0], era[1]).all()


# --- Episode recomputation matches stored report table ------------------------

def test_episode_correlations_match_report(balanced):
    broad = pd.read_parquet(EPISODE_BROAD)
    eras = {f"corr_{name}": (lo, hi) for name, lo, hi in BROAD_ERAS}
    max_dev, checked = 0.0, 0
    for universe, cols in UNIVERSES.items():
        sub = broad[broad["universe"] == universe]
        pooled = A.episode_correlation(balanced, cols, None)
        era_mats = {label: A.episode_correlation(balanced, cols, bounds) for label, bounds in eras.items()}
        for _, row in sub.iterrows():
            a, b = row["asset_i"], row["asset_j"]
            max_dev = max(max_dev, abs(pooled.loc[a, b] - row["corr_stress_pooled"]))
            checked += 1
            for label in eras:
                stored = row[label]
                if pd.notna(stored):
                    max_dev = max(max_dev, abs(era_mats[label].loc[a, b] - stored))
                    checked += 1
    assert checked > 500
    assert max_dev < 1e-9, f"episode recomputation deviates from stored table by {max_dev:.2e}"
