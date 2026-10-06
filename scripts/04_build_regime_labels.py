##### NOTE: DO NOT DELETE



'''
This script develops the regime_labels necessary for the stress definition

- All 12 Tickers for the Asset classes
- The VIX index

NOTE: The functions are defined in src/lsr/loaders/regime_labels.py

This script is mainly developing the classical lables which are for robustness checks regarding the markov switching regime

'''




import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import settings
settings.require_data_dir()

con = duckdb.connect(str(settings.DB_PATH)) # establish the database connection

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "sql" / "schema"

#### 0.0 Constants

QUANTILE = 0.75 # quantile for the windowing and rolling function

####




# 1.0 Get both dataframes in our database

spy = con.execute("""
                  SELECT 
                    date, 
                    price AS spy_close_adj
                  FROM asset_prices 
                  WHERE ticker = 'SPY'
                    AND price_source = 'adj_close'
                  ORDER BY date"""
                  ).fetchdf() # SPY


vix = con.execute("""
                  SELECT date, price AS vix_close_adj
                  FROM vix_quotes
                  WHERE price_source = 'close'
                  ORDER BY date"""
                  ).fetchdf() # VIX

# 1.1 Check datatime for pandas operation
vix["date"] = pd.to_datetime(vix["date"])
spy["date"] = pd.to_datetime(spy["date"])

# 2.0 Merge both tables

regime_data = (spy.merge(vix, on = 'date', how='inner') # inner merge to have a clean data series
               .sort_values("date") 
               .reset_index(drop=True)
)

# 3.0 Pandas Data Operations for the Regime Labels

# 3.1 vix_q75_252 trailing 252-day 75th percentile
regime_data["vix_q75_252"] = (
    regime_data["vix_close_adj"]
    .shift(1) # shift by one day
    .rolling(window=252, min_periods=252)
    .quantile(QUANTILE)  
)

# 3.2 spy_rollmax_252
regime_data["spy_rollmax_252"] = (
    regime_data["spy_close_adj"]
    .rolling(window=252, min_periods=252)
    .max()
)

# 3.3 spy_drawdown -> percentage below rolling high
regime_data["spy_drawdown"] = (
    (regime_data["spy_rollmax_252"] - regime_data["spy_close_adj"])
    / regime_data["spy_rollmax_252"]
)

# 3.4 Robustness -> smoothed Vix version
regime_data["vix_ma21"] = (
    regime_data["vix_close_adj"]
    .rolling(window=21, min_periods=21)
    .mean()
)
regime_data["vix_ma21_q75_252"] = (
    regime_data["vix_ma21"]
    .shift(1)
    .rolling(window=252, min_periods=252)
    .quantile(QUANTILE)
)

# 4.0 Stress Definition
'''
We define Stress via Vix_close > Vix 75-% Quantile + SPY-drawdown >= 5%

For more information please refer to the section 4.1: Regime

'''

# stress_raw
regime_data["stress"] = (
    (regime_data["vix_q75_252"] < regime_data["vix_close_adj"])
    &
    (regime_data["spy_drawdown"] > 0.05)
)

# we define the robustness stress
regime_data["stress_smooth_21d"] = (
    (regime_data["vix_ma21"] > regime_data["vix_ma21_q75_252"]) 
    &
    (regime_data["spy_drawdown"] > 0.05)
)

# 5.0 clean the dataframe and only keep the columns defined in /sql/scheme/04_regime_labels.sql
regime_keep = regime_data.dropna(
    subset=["vix_q75_252", "spy_rollmax_252", "spy_drawdown"]
)

# 5.1 Give human readable names
regime_keep["regime"] = np.where(regime_keep["stress"] == 1, "LB_time", "calm")

# 6.0 Put it into the defined new Table in our Duckdb

## open the DDL scheme
with open(SCHEMA_DIR / "04_regime_labels.sql") as f:
    con.execute(f.read()) # reads the predefined scheme in "sql\schema\04_regime_labels.sql"


df = regime_keep.rename(columns={
        "date":              "date",
        "vix_close_adj":     "vix_close_adj",
        "vix_q75_252":       "vix_q75_252",
        "spy_close_adj":     "spx_close_adj",
        "spy_rollmax_252":   "spx_rollmax_252",
        "spy_drawdown":      "spx_drawdown",
        "stress":            "stress_raw",
        "stress_smooth_21d": "stress_smooth_21d",
        "regime":            "regime"
})[["date", "vix_close_adj", "vix_q75_252", "spx_close_adj", "spx_rollmax_252", "spx_drawdown", "stress_raw", "stress_smooth_21d", "regime"]]

con.execute("INSERT OR IGNORE INTO regime_labels SELECT * from df")




con.close()

