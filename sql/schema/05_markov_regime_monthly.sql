-- Here only DDL is written
/**
We store the official monthly Markov-switching SPY regime in a predefined SQL
database table.

- PRIMARY KEY is the month-end date.
- This table is built by scripts/05_00_build_markov_switching_monthly.py.
- ms_prob_stress = ms_prob_state_{stress_state} where stress_state is the higher-
  variance state from the fitted two-state Markov-switching model.
- ms_stress_50 / ms_stress_75 are the hard labels at 0.5 and 0.75 stress-
  probability thresholds. Downstream code uses ms_stress_50 by default;
  ms_stress_75 is kept as a stricter robustness label.

**/

DROP TABLE IF EXISTS markov_regime_monthly;

CREATE TABLE markov_regime_monthly (
    month_end               DATE PRIMARY KEY,
    spy_monthly_log_return  DOUBLE NOT NULL,
    spy_monthly_return_pct  DOUBLE,
    ms_prob_state_0         DOUBLE NOT NULL CHECK (ms_prob_state_0 BETWEEN 0 AND 1),
    ms_prob_state_1         DOUBLE NOT NULL CHECK (ms_prob_state_1 BETWEEN 0 AND 1),
    calm_state              INTEGER NOT NULL CHECK (calm_state IN (0, 1)),
    stress_state            INTEGER NOT NULL CHECK (stress_state IN (0, 1)),
    ms_prob_stress          DOUBLE NOT NULL CHECK (ms_prob_stress BETWEEN 0 AND 1),
    ms_stress_50            BOOLEAN NOT NULL,
    ms_stress_75            BOOLEAN NOT NULL,
    model_name              VARCHAR NOT NULL,
    model_frequency         VARCHAR NOT NULL,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
