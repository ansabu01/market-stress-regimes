"""Helpers for downloading and validating price data from yfinance."""

import pandas as pd
import yfinance as yf


YFINANCE_PRICE_COLUMNS = {
    "close": "Close",
    "adj_close": "Adj Close",
}


def _validate_ticker(ticker: str) -> str:
    if not isinstance(ticker, str):
        raise TypeError("ticker must be a string.")

    ticker = ticker.strip()

    if ticker == "":
        raise ValueError("ticker cannot be an empty string.")

    return ticker


def _validate_date_range(start: str, end: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    if not isinstance(start, str):
        raise TypeError("start must be a date string in YYYY-MM-DD format.")

    if not isinstance(end, str):
        raise TypeError("end must be a date string in YYYY-MM-DD format.")

    start_date = pd.to_datetime(start, errors="raise")
    end_date = pd.to_datetime(end, errors="raise")

    if start_date >= end_date:
        raise ValueError("start must be before end.")

    return start_date, end_date


def _validate_price_column(price_column: str) -> str:
    if not isinstance(price_column, str):
        raise TypeError("price_column must be a string.")

    price_column = price_column.strip()

    if price_column == "":
        raise ValueError("price_column cannot be an empty string.")

    if price_column not in YFINANCE_PRICE_COLUMNS:
        raise ValueError(
            f"price_column must be one of {sorted(YFINANCE_PRICE_COLUMNS)}. "
            f"Got: {price_column!r}."
        )

    return price_column


def _extract_price_series(
    df: pd.DataFrame,
    ticker: str,
    yfinance_column: str,
) -> pd.Series:
    if isinstance(df.columns, pd.MultiIndex):
        available_columns = list(df.columns)
        available_fields = set(df.columns.get_level_values(0))

        if yfinance_column not in available_fields:
            raise ValueError(
                f"Yahoo Finance column {yfinance_column!r} not found. "
                f"Available columns are: {available_columns}"
            )

        selected = df[yfinance_column]

        if isinstance(selected, pd.DataFrame):
            if ticker in selected.columns:
                return selected[ticker]

            if selected.shape[1] == 1:
                return selected.iloc[:, 0]

            raise ValueError(
                f"Yahoo Finance returned multiple columns for {yfinance_column!r}. "
                f"Available columns are: {list(selected.columns)}"
            )

        return selected

    if yfinance_column not in df.columns:
        raise ValueError(
            f"Yahoo Finance column {yfinance_column!r} not found. "
            f"Available columns are: {list(df.columns)}"
        )

    return df[yfinance_column]


def fetch_yfinance_price(
    ticker: str,
    start: str,
    end: str,
    price_column: str = "adj_close",
) -> pd.DataFrame:
    """
    Fetch one price column for one ticker from yfinance.

    Parameters
    ----------
    ticker : str
        Single ticker symbol, such as "SPY" or "^VIX".
    start : str
        Start date in YYYY-MM-DD format.
    end : str
        End date in YYYY-MM-DD format.
    price_column : str
        Price column to return. Must be "close" or "adj_close".

    Returns
    -------
    pd.DataFrame
        DataFrame indexed by date with columns ["price", "ticker", "price_source"].
    """

    # --- Input checks ---

    ticker = _validate_ticker(ticker)
    start_date, end_date = _validate_date_range(start, end)
    price_column = _validate_price_column(price_column)
    yfinance_column = YFINANCE_PRICE_COLUMNS[price_column]

    # --- Download ---

    df = yf.download(
        tickers=ticker,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        progress=False,
    )

    if df.empty:
        raise ValueError(f"No data returned for ticker: {ticker!r}")

    # --- Select price column ---

    price_series = _extract_price_series(df, ticker, yfinance_column)
    prices = price_series.to_frame(name="price")
    prices["ticker"] = ticker
    prices["price_source"] = price_column

    # --- Date/index checks ---

    date_index = pd.to_datetime(prices.index, errors="coerce")

    if date_index.isna().any():
        raise ValueError("Some index values could not be converted to dates.")

    prices.index = date_index.normalize()
    prices.index.name = "date"

    prices = prices.sort_index()

    if prices.index.has_duplicates:
        duplicate_dates = prices.index[prices.index.duplicated()].unique()
        raise ValueError(f"Duplicate dates found in price data: {list(duplicate_dates)}")

    # --- Data quality checks ---

    prices["price"] = pd.to_numeric(prices["price"], errors="coerce")

    if prices["price"].isna().all():
        raise ValueError(f"No usable {price_column!r} data returned for ticker {ticker!r}.")

    non_positive = prices["price"].dropna() <= 0

    if non_positive.any():
        raise ValueError(
            f"Some {price_column!r} values for ticker {ticker!r} are zero or negative."
        )

    return prices
