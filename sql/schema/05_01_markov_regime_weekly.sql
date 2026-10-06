-- Here only DDL is written
/**
We store the weekly Markov-switching SPY regime (a robustness check on the
official monthly regime) in a predefined SQL database table.

- PRIMARY KEY is the week-end date (last trading day of the week, W-FRI).
- This table is built by scripts/05_01_build_weekly_markov_switching.py.
- ms_prob_stress = ms_prob_state_{stress_state} where stress_state is the higher-
  variance state from the fitted two-state Markov-switching model.
- ms_stress_50 / ms_stress_75 are the hard labels at 0.5 and 0.75 stress-
  probability thresholds. ms_stress_50 (the maximum-probability rule) is primary.

**/

DROP TABLE IF EXISTS markov_regime_weekly;

CREATE TABLE markov_regime_weekly (
    week_end                DATE PRIMARY KEY,
    spy_weekly_log_return   DOUBLE NOT NULL,
    spy_weekly_return_pct   DOUBLE,
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
