"""
Download daily ETF and VIX price data and store it in DuckDB.

Inputs:
- Yahoo Finance price data for the ETF universe
- Yahoo Finance price data for the VIX index

Outputs:
- asset_prices: daily adjusted close prices for the ETF universe
- vix_quotes: daily close levels for the VIX index

Notes:
- Recreates the target DuckDB tables from SQL schema files before inserting data.
- Stores prices in the generic format: date, price, ticker, price_source.
- The date range is controlled by START and END in this script.
"""

from pathlib import Path
import sys

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from settings import DB_PATH, ETF_ASSETS, require_data_dir
from loaders.yfinance_loader import fetch_yfinance_price

SCHEMA_DIR = PROJECT_ROOT / "sql" / "schema"

# ETF universe: the Panel A + Panel B union, bulk-downloaded once.
TICKERS = ETF_ASSETS

# NOTE: Later we will take subsets for seperating the two panels

VIX_TICKER = "^VIX"

START = "2000-01-01"
END = "2025-12-31"


def run_schema(con: duckdb.DuckDBPyConnection, schema_file: str) -> None:
    with open(SCHEMA_DIR / schema_file) as f:
        con.execute(f.read())


def prepare_for_insert(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.reset_index()[["date", "price", "ticker", "price_source"]]


def main() -> None:
    require_data_dir()

    con = duckdb.connect(str(DB_PATH))

    run_schema(con, "01_prices.sql")

    etf_frames = [
        fetch_yfinance_price(
            ticker=ticker,
            start=START,
            end=END,
            price_column="adj_close",
        )
        for ticker in TICKERS
    ]
    etf_prices = prepare_for_insert(pd.concat(etf_frames, axis=0))

    
    con.execute("INSERT OR IGNORE INTO asset_prices SELECT * FROM etf_prices")


    # debugging
    #print(etf_prices[etf_prices['ticker']=='SPY'])
    #print(con.execute("SELECT * FROM asset_prices WHERE ticker = 'SPY' ORDER BY date").fetchdf())
    
    
    run_schema(con, "03_vix_index.sql")

    vix_prices = fetch_yfinance_price(
        ticker=VIX_TICKER,
        start=START,
        end=END,
        price_column="close",
    )
    vix_prices = prepare_for_insert(vix_prices)
    con.execute("INSERT OR IGNORE INTO vix_quotes SELECT * FROM vix_prices")

    etf_count = con.execute("SELECT COUNT(*) FROM asset_prices").fetchone()[0]
    vix_count = con.execute("SELECT COUNT(*) FROM vix_quotes").fetchone()[0]
    con.close()

    print(f"Loaded {etf_count:,} ETF price rows into asset_prices")
    print(f"Loaded {vix_count:,} VIX rows into vix_quotes")
    

if __name__ == "__main__":
    main()
