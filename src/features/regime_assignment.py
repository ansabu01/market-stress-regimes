"""Reusable helpers for broadcasting the monthly Markov label to daily returns.

The orchestration script `scripts/06_assign_monthly_markov_regimes_to_daily_returns.py`
calls into this module. Constants for the ETF universe live here so the
script stays a pure orchestrator.

Example:
    monthly_labels = load_monthly_markov_labels(con)
    etf_returns    = load_etf_daily_log_returns(con)
    etf_labeled    = write_labeled_returns(
        con, etf_returns, monthly_labels, ETF_COLUMNS, ETF_TABLE
    )
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from settings import ETF_ASSETS


# --- constants ---------------------------------------------------------------

MONTHLY_MARKOV_TABLE = "markov_regime_monthly"

ETF_TABLE = "etf_returns_monthly_markov_labeled"

# Project ETF ticker union and source of truth for the ETF labeled-returns DDL.
# Defined once in settings.ETF_ASSETS (Panel A + Panel B, SPY shared); this alias
# names the column set of the labeled table.
ETF_COLUMNS = ETF_ASSETS


# --- private helpers ---------------------------------------------------------


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


# --- public loaders ----------------------------------------------------------


def load_monthly_markov_labels(con) -> pd.DataFrame:
    """Load the official monthly Markov labels used for daily broadcasting."""
    _require_table_columns(
        con,
        MONTHLY_MARKOV_TABLE,
        {"month_end", "ms_stress_50", "ms_prob_stress"},
    )

    labels = con.execute(
        f"""
        SELECT
            month_end AS date,
            CAST(ms_stress_50 AS INTEGER) AS ms_stress,
            ms_prob_stress
        FROM {MONTHLY_MARKOV_TABLE}
        ORDER BY month_end
        """
    ).fetchdf()

    if labels.empty:
        raise RuntimeError(f"{MONTHLY_MARKOV_TABLE} is empty.")
    if labels["date"].duplicated().any():
        raise RuntimeError(f"{MONTHLY_MARKOV_TABLE} contains duplicate dates.")

    values = set(labels["ms_stress"].dropna().astype(int).unique())
    if not values.issubset({0, 1}):
        raise RuntimeError(f"ms_stress must contain only 0/1 values. Found: {sorted(values)}")

    return labels


def load_etf_daily_log_returns(con) -> pd.DataFrame:
    """Load ETF adjusted closes and return daily log returns in wide format."""
    _require_table_columns(con, "asset_prices", {"date", "ticker", "price", "price_source"})

    prices = con.execute(
        """
        SELECT
            date,
            ticker,
            price AS adj_close
        FROM asset_prices
        WHERE price_source = 'adj_close'
        ORDER BY ticker, date
        """
    ).fetchdf()

    if prices.empty:
        raise RuntimeError("asset_prices is empty.")
    if (prices["adj_close"] <= 0).any():
        raise RuntimeError("asset_prices.adj_close contains non-positive values.")

    prices["date"] = pd.to_datetime(prices["date"])
    prices["log_return"] = prices.groupby("ticker")["adj_close"].transform(
        lambda values: np.log(values).diff()
    )

    returns = prices.pivot(index="date", columns="ticker", values="log_return")
    returns = returns.sort_index().dropna(axis=0, how="all").reset_index()
    returns.columns.name = None
    return returns


# --- public actions ----------------------------------------------------------


def assign_monthly_regime_to_daily_returns(
    daily_returns: pd.DataFrame,
    monthly_markov_labels: pd.DataFrame,
) -> pd.DataFrame:
    """Broadcast monthly Markov labels (ms_stress, ms_prob_stress) onto daily rows."""
    daily = daily_returns.copy()
    monthly = monthly_markov_labels[["date", "ms_stress", "ms_prob_stress"]].copy()

    daily["date"] = pd.to_datetime(daily["date"])
    monthly["date"] = pd.to_datetime(monthly["date"])

    daily["month"] = daily["date"].dt.to_period("M")
    monthly["month"] = monthly["date"].dt.to_period("M")

    labeled = daily.merge(
        monthly[["month", "ms_stress", "ms_prob_stress"]],
        on="month",
        how="left", # dont keep non index rows (shouldnt exist in the first place)
    )

    return labeled.drop(columns="month")


def validate_labeled_returns(df: pd.DataFrame, table_name: str) -> None:
    """Validate the labeled wide return table before database insertion."""
    if df.empty:
        raise RuntimeError(f"{table_name} would be empty.")
    if "month" in df.columns:
        raise RuntimeError(f"{table_name} still contains a temporary month column.")
    if df["date"].duplicated().any():
        raise RuntimeError(f"{table_name} contains duplicate dates.")

    values = set(df["ms_stress"].dropna().astype(int).unique()) # Labels MUST BE UNIQUE
    if not values.issubset({0, 1}):
        raise RuntimeError(f"{table_name}.ms_stress must contain only 0/1 values.")


def write_labeled_returns(
    con,
    returns_df: pd.DataFrame,
    monthly_labels: pd.DataFrame,
    columns: list[str],
    table_name: str,
) -> pd.DataFrame:
    """Label daily returns with the monthly Markov state and INSERT into table_name.

    Returns the labeled DataFrame so callers can compute summaries without
    re-querying. The schema for `table_name` must already exist.
    """
    labeled = assign_monthly_regime_to_daily_returns(returns_df, monthly_labels)
    labeled = labeled.dropna(subset=["ms_stress", "ms_prob_stress"]).copy()

    labeled["ms_stress"] = labeled["ms_stress"].astype(int)
    labeled["date"] = pd.to_datetime(labeled["date"]).dt.date

    validate_labeled_returns(labeled, table_name)

    insert_columns = ["date", *columns, "ms_stress", "ms_prob_stress"]

    column_list = ", ".join(insert_columns)

    con.execute(
        f"INSERT OR IGNORE INTO {table_name} ({column_list}) "
        f"SELECT {column_list} FROM labeled"
    )
    return labeled
