-- Store ETF prices downloaded from Yahoo Finance.
-- Executed by scripts/02_fetch_market_prices.py.

DROP TABLE IF EXISTS asset_prices;
CREATE TABLE asset_prices (
    date        DATE,
    price       DOUBLE,
    ticker      VARCHAR,
    price_source VARCHAR,
    PRIMARY KEY (date, ticker, price_source),
    CHECK (price > 0),
    CHECK (price_source IN ('close', 'adj_close'))
);
