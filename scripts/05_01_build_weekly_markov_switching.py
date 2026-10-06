##### NOTE: DO NOT DELETE


"""
Build the weekly Markov-switching SPY regime (robustness check).

We fit the SAME two-state Markov-switching model (switching mean and variance)
used for the official monthly regime, but on weekly SPY log returns (last
trading day of each week, W-FRI). The state with the higher fitted variance is
the stress state.

This is a robustness check on scripts/05_00_build_markov_switching_monthly.py: it
shows the regime is not an artifact of the monthly sampling frequency. The
monthly regime remains the official label.

PLEASE NOTE: The data can be imbalanced since we only take: WEEK-YEAR as the key we are ignoring different trading days within weeks or holidays

NOTE: Run scripts/02_fetch_market_prices.py and scripts/04_build_regime_labels.py
before this script.

Please note that we have common functions defined in src/regimes for any kind of frequency we might choose for the markov regimes.

"""


import sys
from pathlib import Path

sys.path.insert(0, "src")

import duckdb

import settings

# NOTE: We import all our functions from the src/regimes

from regimes.markov_switching import (
    WEEKLY,
    build_markov_frequency_comparison,
    build_markov_model_summary,
    build_markov_regime_table,
    build_markov_vs_defined_comparison,
    build_periodic_spy_returns,
    extract_state_variances,
    fit_markov_switching_model,
    identify_stress_state,
    load_spy_prices,
    write_markov_outputs,
)


settings.require_data_dir() # ensure directly is available


con = duckdb.connect(str(settings.DB_PATH)) # connect to the database
SCHEMA_DIR = Path(__file__).resolve().parents[1] / "sql" / "schema"


# 1.0 Execute the DDL schemes
for schema_file in ("05_01_markov_regime_weekly.sql", "05_01_markov_weekly_model_summary.sql"):
    with open(SCHEMA_DIR / schema_file) as f: 
        con.execute(f.read())


# 2.0 Load SPY and build weekly returns
spy_prices = load_spy_prices(con) # loads the prices from the SPY
weekly_returns = build_periodic_spy_returns(spy_prices, WEEKLY) # indexes with WEEK-YEAR and builds an indexed version of the SPY


# 3.0 Fit the Markov-switching model and identify the stress state
results = fit_markov_switching_model(weekly_returns, WEEKLY) # We fit the markov model via the statsmodels library
state_variances = extract_state_variances(results)           # depending on k (states) we extract the model.params from the fitted model and retrieve the variance
stress_state = identify_stress_state(state_variances)        # we take the variance with the higher state


# 4.0 Build and write the regime and summary tables
regime_df = build_markov_regime_table(weekly_returns, results, stress_state, WEEKLY)
summary_df = build_markov_model_summary(results, weekly_returns, stress_state, WEEKLY)
write_markov_outputs(con, regime_df, summary_df, WEEKLY)


# 5.0 Robustness diagnostics: agreement with rule-based labels and with monthly
defined_comparison = build_markov_vs_defined_comparison(con, WEEKLY)
frequency_comparison = build_markov_frequency_comparison(con)

'''
Please uncomment the following code for a summary table when running this script
'''
# # 6.0 Short summary only
# print(
#     f"markov_regime_weekly rows: {len(regime_df):,}  "
#     f"({regime_df['week_end'].min()} -> {regime_df['week_end'].max()})  "
#     f"stress state: {stress_state}  "
#     f"ms_stress_50 share: {regime_df['ms_stress_50'].mean():.2%}  "
#     f"ms_stress_75 share: {regime_df['ms_stress_75'].mean():.2%}"
# )


con.close()
