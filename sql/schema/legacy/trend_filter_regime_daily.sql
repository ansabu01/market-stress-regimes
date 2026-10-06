-- Here only DDL is written
/**
We store the trend-filter robustness regime in a predefined SQL database table.

- This regime is a robustness check, not the official regime label.
- The official monthly regime lives in markov_regime_monthly (see 05_markov_regime_monthly.sql).
- PRIMARY KEY is the date (Datetime).
- This table is built by legacy/05_build_trend_filter_regime.py.
- The trend filter smooths log(VIX) and SPY drawdown before forming a stable stress label.

**/

DROP TABLE IF EXISTS trend_filter_regime_daily;

CREATE TABLE trend_filter_regime_daily (
    date                   DATE PRIMARY KEY,
    spy_close_adj          DOUBLE NOT NULL,
    vix_close_adj          DOUBLE NOT NULL,
    spy_drawdown_raw       DOUBLE,
    spy_drawdown_trend     DOUBLE,
    vix_log                DOUBLE,
    vix_trend              DOUBLE,
    vix_trend_q75_252_lag  DOUBLE,
    stress_trend_raw       INTEGER NOT NULL CHECK (stress_trend_raw IN (0, 1)),
    stress_trend_stable    INTEGER NOT NULL CHECK (stress_trend_stable IN (0, 1)),
    episode_id             INTEGER,
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
