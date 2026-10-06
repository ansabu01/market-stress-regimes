-- Here only DDL is written
/**
We store one summary row per (universe, method) describing the distribution of
pairwise correlations in calm vs stress regimes.

- PRIMARY KEY is (universe, method).
- This table is built by scripts/07_build_regime_correlations.py.
- *_diff columns are stress-minus-calm statistics, so they live in [-2, 2];
  plain calm/stress statistics live in [-1, 1].

**/

DROP TABLE IF EXISTS correlation_summary;

CREATE TABLE correlation_summary (
    universe            VARCHAR NOT NULL,
    method              VARCHAR NOT NULL,
    n_assets            INTEGER NOT NULL CHECK (n_assets >= 2),
    n_pairs             INTEGER NOT NULL CHECK (n_pairs >= 1),
    n_calm_days         INTEGER NOT NULL CHECK (n_calm_days >= 2),
    n_stress_days       INTEGER NOT NULL CHECK (n_stress_days >= 2),
    avg_corr_calm       DOUBLE NOT NULL CHECK (avg_corr_calm BETWEEN -1 AND 1),
    avg_corr_stress     DOUBLE NOT NULL CHECK (avg_corr_stress BETWEEN -1 AND 1),
    avg_corr_diff       DOUBLE NOT NULL CHECK (avg_corr_diff BETWEEN -2 AND 2),
    median_corr_calm    DOUBLE NOT NULL CHECK (median_corr_calm BETWEEN -1 AND 1),
    median_corr_stress  DOUBLE NOT NULL CHECK (median_corr_stress BETWEEN -1 AND 1),
    median_corr_diff    DOUBLE NOT NULL CHECK (median_corr_diff BETWEEN -2 AND 2),
    p10_corr_calm       DOUBLE NOT NULL CHECK (p10_corr_calm BETWEEN -1 AND 1),
    p10_corr_stress     DOUBLE NOT NULL CHECK (p10_corr_stress BETWEEN -1 AND 1),
    p10_corr_diff       DOUBLE NOT NULL CHECK (p10_corr_diff BETWEEN -2 AND 2),
    p90_corr_calm       DOUBLE NOT NULL CHECK (p90_corr_calm BETWEEN -1 AND 1),
    p90_corr_stress     DOUBLE NOT NULL CHECK (p90_corr_stress BETWEEN -1 AND 1),
    p90_corr_diff       DOUBLE NOT NULL CHECK (p90_corr_diff BETWEEN -2 AND 2),
    min_corr_calm       DOUBLE NOT NULL CHECK (min_corr_calm BETWEEN -1 AND 1),
    min_corr_stress     DOUBLE NOT NULL CHECK (min_corr_stress BETWEEN -1 AND 1),
    max_corr_calm       DOUBLE NOT NULL CHECK (max_corr_calm BETWEEN -1 AND 1),
    max_corr_stress     DOUBLE NOT NULL CHECK (max_corr_stress BETWEEN -1 AND 1),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (universe, method)
);
