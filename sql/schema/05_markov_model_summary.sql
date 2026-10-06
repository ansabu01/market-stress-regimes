-- Here only DDL is written
/**
We store one row per fitted Markov-switching model so downstream code can read
the model specification, sample range, fitted variances, and information
criteria without re-fitting.

- PRIMARY KEY is the model_name.
- This table is built by scripts/05_00_build_markov_switching_monthly.py.
- A row is written every time the script runs; the INSERT OR IGNORE in the
  script keeps the first row when re-run on a populated database. Drop the
  table to refresh.

**/

DROP TABLE IF EXISTS markov_model_summary;

CREATE TABLE markov_model_summary (
    model_name          VARCHAR PRIMARY KEY,
    model_frequency     VARCHAR NOT NULL,
    sample_start        DATE NOT NULL,
    sample_end          DATE NOT NULL,
    n_observations      INTEGER NOT NULL,
    k_regimes           INTEGER NOT NULL,
    trend_spec          VARCHAR NOT NULL,
    switching_variance  BOOLEAN NOT NULL,
    state_0_variance    DOUBLE,
    state_1_variance    DOUBLE,
    calm_state          INTEGER NOT NULL,
    stress_state        INTEGER NOT NULL,
    log_likelihood      DOUBLE,
    aic                 DOUBLE,
    bic                 DOUBLE,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
