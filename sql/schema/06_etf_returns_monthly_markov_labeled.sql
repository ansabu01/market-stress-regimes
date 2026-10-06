-- Here only DDL is written
/**
We store daily ETF log returns broadcast with the monthly Markov stress label.

- PRIMARY KEY is the date (one row per trading day).
- This table is built by scripts/06_assign_monthly_markov_regimes_to_daily_returns.py.
- The ticker columns hold daily log returns for the project's ETF universe
  (PANEL_A union PANEL_B, defined by src/settings/tickers.py).
- ms_stress is taken from markov_regime_monthly.ms_stress_50 and broadcast to
  every trading day inside the same calendar month.

**/

DROP TABLE IF EXISTS etf_returns_monthly_markov_labeled;

CREATE TABLE etf_returns_monthly_markov_labeled (
    date            DATE PRIMARY KEY,
    AGG             DOUBLE,
    DBC             DOUBLE,
    EEM             DOUBLE,
    EFA             DOUBLE,
    EWG             DOUBLE,
    EWJ             DOUBLE,
    EWU             DOUBLE,
    GLD             DOUBLE,
    HYG             DOUBLE,
    SHY             DOUBLE,
    SPY             DOUBLE,
    TLT             DOUBLE,
    USO             DOUBLE,
    VNQ             DOUBLE,
    ms_stress       INTEGER NOT NULL CHECK (ms_stress IN (0, 1)),
    ms_prob_stress  DOUBLE NOT NULL CHECK (ms_prob_stress BETWEEN 0 AND 1),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
