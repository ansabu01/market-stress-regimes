"""
Build canonical regime-conditional correlation tables.

For each universe (Panel A cross-asset, Panel B international equity, and the
combined etf_assets union) we compute calm, stress, and stress-minus-calm
Pearson correlation matrices and persist a one-row summary plus the long pair
table. Every universe is restricted to the common balanced window (the dates on
which all combined-universe assets are observed) so the portfolio-level
aggregates share the same trading days; this matches the PCA build (scripts/08)
and is required by the Forbes-Rigobon build (scripts/09), which loads the
per-panel correlations back out of correlation_pairs.

Heatmap plotting lives in notebooks/03_correlation_raw_full_pipeline.ipynb.

NOTE: Run scripts/06_assign_monthly_markov_regimes_to_daily_returns.py before
this script.
"""


import sys
from pathlib import Path

sys.path.insert(0, "src")

import duckdb
import pandas as pd

import settings
from analysis.regime_correlations import (
    build_universe_correlation_outputs,
    common_complete_case_dates,
    prepare_labeled_returns,
    write_correlation_outputs,
)
from features.regime_assignment import ETF_TABLE

CORRELATION_UNIVERSES = (
    ("panel_a_cross_asset", settings.PANEL_A),
    ("panel_b_international_equity", settings.PANEL_B),
    ("etf_assets", settings.ETF_ASSETS),
)


settings.require_data_dir()
con = duckdb.connect(str(settings.DB_PATH))
SCHEMA_DIR = Path(__file__).resolve().parents[1] / "sql" / "schema"


# 1.0 Execute the DDL schemes
for schema_file in ("07_correlation_summary.sql", "07_correlation_pairs.sql"):
    with open(SCHEMA_DIR / schema_file) as f:
        con.execute(f.read())


# 2.0 Load labeled returns once and pin the common balanced window so every
#     universe is summarised on identical trading days.
raw_labeled = con.execute(f"SELECT * FROM {ETF_TABLE} ORDER BY date").fetchdf()
raw_labeled["date"] = pd.to_datetime(raw_labeled["date"])
common_dates = common_complete_case_dates(raw_labeled, list(settings.ETF_ASSETS))


# 3.0 Build correlation outputs per universe on that window.
summary_frames = []
pair_frames = []
for universe, requested_columns in CORRELATION_UNIVERSES:
    columns = [c for c in requested_columns if c in raw_labeled.columns]
    data = prepare_labeled_returns(raw_labeled, columns, restrict_dates=common_dates)
    summary, pairs = build_universe_correlation_outputs(data, columns, universe)
    summary_frames.append(summary)
    pair_frames.append(pairs)

summary = pd.concat(summary_frames, ignore_index=True)
print(summary)
pairs = pd.concat(pair_frames, ignore_index=True)
print(pairs)

# 4.0 Write outputs
write_correlation_outputs(con, summary, pairs)


# 5.0 Short summary only
deltas = ", ".join(
    f"{row.universe}={row.avg_corr_diff:+.3f}" for row in summary.itertuples(index=False)
)
print(
    f"correlations: {len(summary)} universes, {len(pairs):,} pair rows, "
    f"avg stress_minus_calm corr: {deltas}"
)

con.close()
