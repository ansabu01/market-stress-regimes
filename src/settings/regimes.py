from pathlib import Path

from settings.paths import PROJECT_ROOT


# --- Trend filter smoothness -------------------------------------------------

# Larger values make the VIX trend smoother.
VIX_LAM: float = 45.0

# Larger values make the S&P 500 drawdown trend smoother.
DRAWDOWN_LAM: float = 30.0

# 0 = piecewise constant trend, 1 = piecewise linear trend.
TREND_DEGREE: int = 1

# Keep this True so lambda values are easier to compare across series.
STANDARDIZE_INPUTS: bool = True


# --- Stress definition after smoothing ---------------------------------------

# VIX trend must be above this trailing quantile to count as stress.
VIX_QUANTILE: float = 0.75

# Number of trading days used for the trailing VIX trend threshold.
VIX_QUANTILE_WINDOW: int = 252

# S&P 500 trend-filtered drawdown must be above this level to count as stress.
DRAWDOWN_THRESHOLD: float = 0.05


# --- Regime stability rules --------------------------------------------------

# Remove stress episodes shorter than this many trading days.
MIN_STRESS_DAYS: int = 30

# Fill calm gaps shorter than this many trading days inside stress episodes.
MIN_CALM_DAYS: int = 10


# --- Database table settings -------------------------------------------------

TREND_FILTER_TABLE: str = "trend_filter_regime_daily"

TREND_FILTER_SCHEMA_PATH: Path = (
    PROJECT_ROOT / "sql" / "schema" / "legacy" / "trend_filter_regime_daily.sql"
)
