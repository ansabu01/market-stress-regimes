##### NOTE: DO NOT DELETE


"""
Build the official monthly Markov-switching SPY regime.

We fit a two-state Markov-switching model (switching mean and variance) on
monthly SPY log returns. The state with the higher fitted variance is the
stress state. This is the BIC-preferred specification (see the robustness
build in scripts/05_01_build_weekly_markov_switching.py and notebook 02).

This is the official regime label. 

NOTE: Run scripts/02_fetch_market_prices.py before this script.
"""


import sys
from pathlib import Path

sys.path.insert(0, "src")

import duckdb

import settings
from regimes.markov_switching import (
    build_markov_model_summary,
    build_markov_regime_table,
    build_markov_vs_defined_comparison,
    build_monthly_spy_returns,
    extract_state_variances,
    fit_markov_switching_model,
    identify_stress_state,
    load_spy_prices,
    write_markov_outputs,
)


settings.require_data_dir()
con = duckdb.connect(str(settings.DB_PATH))
SCHEMA_DIR = Path(__file__).resolve().parents[1] / "sql" / "schema"


# 1.0 Execute the DDL schemes
for schema_file in ("05_markov_regime_monthly.sql", "05_markov_model_summary.sql"):
    with open(SCHEMA_DIR / schema_file) as f:
        con.execute(f.read())


# 2.0 Load SPY and build monthly returns
spy_prices = load_spy_prices(con)
monthly_returns = build_monthly_spy_returns(spy_prices)


# 3.0 Fit the Markov-switching model and identify the stress state
results = fit_markov_switching_model(monthly_returns)
state_variances = extract_state_variances(results) # for k = 2 we will have exactly two variances -> Higher for stress
stress_state = identify_stress_state(state_variances) # Will just pick the MAX() of all state variances


# 4.0 Build and write the regime and summary tables
regime_df = build_markov_regime_table(monthly_returns, results, stress_state)
summary_df = build_markov_model_summary(results, monthly_returns, stress_state)
write_markov_outputs(con, regime_df, summary_df)


# 5.0 Robustness: agreement with the rule-based (VIX + drawdown) daily labels
comparison_df = build_markov_vs_defined_comparison(con)


con.close()
