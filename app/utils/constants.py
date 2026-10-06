"""Canonical constants for the Stress-Regime dashboard.

Universes, asset labels, stress-episode definitions, and Forbes-Rigobon
interpretation classes are defined once here so no page re-hardcodes them.
This module is pure (no Streamlit / IO) and safe to import from tests.
"""

from __future__ import annotations

# --- Asset universes (mirror src/settings/tickers.py; SPY shared, listed once) ---

PANEL_A: list[str] = ["SPY", "SHY", "TLT", "AGG", "HYG", "GLD", "DBC", "USO", "VNQ"]
PANEL_B: list[str] = ["SPY", "EFA", "EEM", "EWG", "EWU", "EWJ"]
ETF_ASSETS: list[str] = list(dict.fromkeys(PANEL_A + PANEL_B))  # 14, Panel A order then B extras

UNIVERSES: dict[str, list[str]] = {
    "panel_a_cross_asset": PANEL_A,
    "panel_b_international_equity": PANEL_B,
    "etf_assets": ETF_ASSETS,
}

UNIVERSE_LABELS: dict[str, str] = {
    "panel_a_cross_asset": "Panel A · Cross-asset",
    "panel_b_international_equity": "Panel B · International equity",
    "etf_assets": "Combined ETF universe",
}

# Short human-readable name for each ETF (used in tables / hovers / selectors).
ASSET_LABELS: dict[str, str] = {
    "SPY": "US equity (SPY)",
    "SHY": "Short Treasuries (SHY)",
    "TLT": "Long Treasuries (TLT)",
    "AGG": "US aggregate bonds (AGG)",
    "HYG": "US high-yield credit (HYG)",
    "GLD": "Gold (GLD)",
    "DBC": "Broad commodities (DBC)",
    "USO": "Crude oil (USO)",
    "VNQ": "US real estate (VNQ)",
    "EFA": "Developed ex-US equity (EFA)",
    "EEM": "Emerging-market equity (EEM)",
    "EWG": "Germany equity (EWG)",
    "EWU": "UK equity (EWU)",
    "EWJ": "Japan equity (EWJ)",
}

# Coarse asset-class role for deterministic interpretation logic.
ASSET_ROLE: dict[str, str] = {
    "SPY": "equity", "EFA": "equity", "EEM": "equity",
    "EWG": "equity", "EWU": "equity", "EWJ": "equity",
    "SHY": "treasury", "TLT": "treasury",
    "AGG": "bond", "HYG": "credit",
    "GLD": "gold", "DBC": "commodity", "USO": "commodity",
    "VNQ": "real_estate",
}


# --- Stress-episode definitions (official Markov stress days by calendar era) ---
# Boundaries and the 100-day reporting floor match notebook 03 and the report
# appendix (tab:stress_episode_hedges). 2024-2025 sits below the floor.

MIN_EPISODE_STRESS_DAYS: int = 100

BROAD_ERAS: list[tuple[str, int, int]] = [
    ("2007-2019", 2007, 2019),
    ("2020-2021", 2020, 2021),
    ("2022-2023", 2022, 2023),
    ("2024-2025", 2024, 2025),
]

# Episode selector options for the Stress Anatomy page (pooled + the reportable eras).
PRIMARY_EPISODES: list[str] = ["Pooled stress", "2007-2019", "2020-2021", "2022-2023"]

EPISODE_DESCRIPTIONS: dict[str, str] = {
    "Pooled stress": "All official Markov stress days in the balanced window.",
    "2007-2019": "Global financial crisis, euro-area stress, and the late cycle.",
    "2020-2021": "The COVID-19 shock and its recovery.",
    "2022-2023": "The inflation and rate-hike drawdown.",
    "2024-2025": "Recent stress (below the 100-day reporting floor).",
}

# Default hedge pairs for the Stress Anatomy hedge-behaviour comparison.
DEFAULT_HEDGE_PAIRS: list[tuple[str, str]] = [
    ("SPY", "TLT"),
    ("SPY", "AGG"),
    ("SPY", "GLD"),
    ("SPY", "VNQ"),
    ("TLT", "AGG"),
    ("TLT", "VNQ"),
]

# Default Portfolio X-Ray selection (a mixed cross-asset sleeve).
DEFAULT_PORTFOLIO: list[str] = ["SPY", "TLT", "GLD", "HYG", "VNQ"]


# --- Forbes-Rigobon fragility taxonomy (verbatim class strings from the pipeline) ---

FR_ROBUST = "Robust breakdown after adjustment"
FR_VOL_SENSITIVE = "Volatility-bias-sensitive increase"
FR_RESILIENT = "Resilient: correlation decreased in stress"
FR_MOSTLY_RESILIENT = "Mostly resilient / small adjusted increase"
FR_UNAVAILABLE = "Adjustment unavailable"

FR_CLASS_ORDER: list[str] = [
    FR_ROBUST,
    FR_VOL_SENSITIVE,
    FR_MOSTLY_RESILIENT,
    FR_RESILIENT,
    FR_UNAVAILABLE,
]

FR_METHOD_LABELS: dict[str, str] = {
    "market_spy": "SPY market shock (main)",
    "pair_max": "Pair-max (conservative)",
}


def universe_columns(universe: str) -> list[str]:
    """Return the ordered ticker list for a universe key."""
    if universe not in UNIVERSES:
        raise KeyError(f"Unknown universe: {universe!r}. Expected one of {list(UNIVERSES)}.")
    return list(UNIVERSES[universe])


def pretty_pair(asset_i: str, asset_j: str) -> str:
    """Human-readable pair label, e.g. 'SPY–TLT'."""
    return f"{asset_i}–{asset_j}"
