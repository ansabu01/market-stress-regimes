##### NOTE: DO NOT DELETE

"""
Build PCA-based regime concentration metrics from raw correlation matrices.

The script persists only the three PCA result tables. Figures and display logic
belong in notebooks/05_pca.ipynb.

Run from the project root:

    python scripts/08_build_pca_regime_concentration.py
"""


import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, "src")

import settings
from analysis.pca_concentration import (
    build_universe_outputs,
    common_complete_case_dates,
    load_labeled_return_table,
    prepare_labeled_returns,
    write_pca_outputs,
)
from features.regime_assignment import ETF_TABLE

PCA_UNIVERSES = (
    ("panel_a_cross_asset", settings.PANEL_A),
    ("panel_b_international_equity", settings.PANEL_B),
    ("etf_assets", settings.ETF_ASSETS),
)


settings.require_data_dir()
con = duckdb.connect(str(settings.DB_PATH))
SCHEMA_DIR = Path(__file__).resolve().parents[1] / "sql" / "schema"


# 1.0 Execute the DDL schemes
for schema_file in (
    "08_pca_regime_concentration_eigenvalues.sql",
    "08_pca_regime_concentration_summary.sql",
    "08_pca_regime_concentration_comparison.sql",
):
    with open(SCHEMA_DIR / schema_file) as f:
        con.execute(f.read())


# 2.0 Load labeled returns once and build PCA outputs per universe.
# Every universe is restricted to the common balanced window (the dates where all
# combined-universe assets are observed) so the concentration measures share the
# same trading days; only Panel B is shortened by this.
raw_data = load_labeled_return_table(con, ETF_TABLE)
common_dates = common_complete_case_dates(raw_data, list(settings.ETF_ASSETS))
eig_frames = []
sum_frames = []
cmp_frames = []
for universe, requested_columns in PCA_UNIVERSES:
    data, return_columns = prepare_labeled_returns(
        raw_data,
        requested_columns,
        source_name=f"{ETF_TABLE}/{universe}",
        restrict_dates=common_dates,
    )
    eigenvalues, summary, comparison = build_universe_outputs(universe, data, return_columns)
    eig_frames.append(eigenvalues)
    sum_frames.append(summary)
    cmp_frames.append(comparison)


# 3.0 Concatenate and write outputs
eigenvalues = pd.concat(eig_frames, ignore_index=True)
summary = pd.concat(sum_frames, ignore_index=True)
comparison = pd.concat(cmp_frames, ignore_index=True)
write_pca_outputs(con, eigenvalues, summary, comparison)


# 4.0 Short summary only
deltas = ", ".join(
    f"{row.universe}={row.stress_minus_calm_pc1_share:+.3f}"
    for row in comparison.itertuples(index=False)
)
print(
    f"pca: {len(PCA_UNIVERSES)} universes, "
    f"{len(eigenvalues)} eigenvalue rows, "
    f"stress_minus_calm pc1_share: {deltas}"
)

con.close()
