##### NOTE: DO NOT DELETE

"""Build the Forbes-Rigobon tables and their main comparison figure.

The statistical and data-preparation functions live in
``src/analysis/forbes_rigobon.py``. This script only runs those functions in
the correct order, following the same structure as the Markov build scripts.

Raw correlations are loaded from the database output of script 07 and are not
calculated a second time.
"""

import sys
from pathlib import Path

sys.path.insert(0, "src")

import duckdb
import pandas as pd

import settings
from analysis.forbes_rigobon import (
    build_all_forbes_rigobon_outputs,
    plot_raw_vs_adjusted_changes,
    write_outputs,
)
from analysis.regime_correlations import common_complete_case_dates
from features.regime_assignment import ETF_TABLE


settings.require_data_dir()
con = duckdb.connect(str(settings.DB_PATH))
SCHEMA_DIR = Path(__file__).resolve().parents[1] / "sql" / "schema"

FR_UNIVERSES = [
    ("panel_a_cross_asset", settings.PANEL_A),
    ("panel_b_international_equity", settings.PANEL_B),
    ("etf_assets", settings.ETF_ASSETS),
]


# 1.0 Load regime-labelled daily returns and the common balanced window.
raw_labeled = con.execute(f"SELECT * FROM {ETF_TABLE} ORDER BY date").fetchdf()
raw_labeled["date"] = pd.to_datetime(raw_labeled["date"])
common_dates = common_complete_case_dates(raw_labeled, list(settings.ETF_ASSETS))


# 2.0 Build variance ratios, adjusted pairs, and summary for every universe on
#     that common window, so the variance shocks and the raw correlations they
#     adjust are measured on identical trading days. Raw correlations come from
#     the correlation_pairs table created by script 07 and are not recalculated.
variance_ratios, adjusted_pairs, summary = build_all_forbes_rigobon_outputs(
    con,
    raw_labeled,
    FR_UNIVERSES,
    restrict_dates=common_dates,
)


# 4.0 Recreate the three output tables from their explicit SQL schemas.
for schema_file in (
    "09_forbes_rigobon_variance_ratios.sql",
    "09_forbes_rigobon_adjusted_pairs.sql",
    "09_forbes_rigobon_adjusted_summary.sql",
):
    con.execute((SCHEMA_DIR / schema_file).read_text())


# 5.0 Store the calculated results in DuckDB.
write_outputs(con, variance_ratios, adjusted_pairs, summary)


# 6.0 Create the main raw-versus-adjusted comparison figure for the combined ETF
#     universe (the notebook produces the richer per-universe plotnine figures).
figure_path = (
    settings.PROJECT_ROOT
    / "outputs"
    / "06_adjusted_correlation"
    / "forbes_rigobon_raw_vs_adjusted.png"
)
plot_raw_vs_adjusted_changes(
    adjusted_pairs[adjusted_pairs["universe"] == "etf_assets"],
    figure_path,
)


# 7.0 Print a short run summary and close the database connection.
spy_delta = variance_ratios.loc[
    variance_ratios["asset"] == "SPY",
    "fr_delta",
].iloc[0]
print(
    f"forbes_rigobon: SPY variance delta {spy_delta:.3f}, "
    f"{len(adjusted_pairs):,} adjusted pair rows, figure: {figure_path}"
)
con.close()
