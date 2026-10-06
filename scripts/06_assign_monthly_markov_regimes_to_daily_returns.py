##### NOTE: DO NOT DELETE


"""
Assign monthly Markov regime labels to the daily ETF return table.

This is the daily-label broadcast step. Each trading day inside a calendar
month inherits that month's ms_stress / ms_prob_stress from
markov_regime_monthly (using the ms_stress_50 threshold as the official label).

NOTE: Run scripts/05_00_build_markov_switching_monthly.py before this script.
"""


import sys
from pathlib import Path

sys.path.insert(0, "src")

import duckdb

import settings
from features.regime_assignment import (
    ETF_COLUMNS,
    ETF_TABLE,
    load_etf_daily_log_returns,
    load_monthly_markov_labels,
    write_labeled_returns,
)


settings.require_data_dir()
con = duckdb.connect(str(settings.DB_PATH))
SCHEMA_DIR = Path(__file__).resolve().parents[1] / "sql" / "schema"


# 1.0 Execute the DDL scheme
with open(SCHEMA_DIR / f"06_{ETF_TABLE}.sql") as f:
    con.execute(f.read())


# 2.0 Load monthly labels and daily returns
monthly_labels = load_monthly_markov_labels(con)
etf_returns = load_etf_daily_log_returns(con)


# 3.0 Label and write the ETF universe
etf_labeled = write_labeled_returns(con, etf_returns, monthly_labels, ETF_COLUMNS, ETF_TABLE)


# 4.0 Short summary only
print(
    f"{ETF_TABLE} rows: {len(etf_labeled):,}  "
    f"stress share: {etf_labeled['ms_stress'].mean():.2%}"
)

con.close()
