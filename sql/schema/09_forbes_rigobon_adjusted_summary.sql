-- Here only DDL is written
/**
We store classification counts of the Forbes-Rigobon adjusted pairs per
(universe, fr_method).

- PRIMARY KEY is (universe, fr_method).
- This table is built by scripts/09_build_forbes_rigobon_adjusted_correlations.py.

**/

DROP TABLE IF EXISTS forbes_rigobon_adjusted_summary;

CREATE TABLE forbes_rigobon_adjusted_summary (
    universe                         VARCHAR NOT NULL,
    fr_method                        VARCHAR NOT NULL CHECK (fr_method IN ('market_spy', 'pair_max')),
    adjusted_rows                    INTEGER NOT NULL CHECK (adjusted_rows > 0),
    available_rows                   INTEGER NOT NULL CHECK (available_rows >= 0),
    unavailable_rows                 INTEGER NOT NULL CHECK (unavailable_rows >= 0),
    avg_delta_corr                   DOUBLE NOT NULL CHECK (avg_delta_corr BETWEEN -2 AND 2),
    median_delta_corr                DOUBLE NOT NULL CHECK (median_delta_corr BETWEEN -2 AND 2),
    avg_delta_corr_adjusted          DOUBLE CHECK (avg_delta_corr_adjusted BETWEEN -2 AND 2),
    median_delta_corr_adjusted       DOUBLE CHECK (median_delta_corr_adjusted BETWEEN -2 AND 2),
    robust_breakdown_count           INTEGER NOT NULL CHECK (robust_breakdown_count >= 0),
    volatility_bias_sensitive_count  INTEGER NOT NULL CHECK (volatility_bias_sensitive_count >= 0),
    resilient_decreased_count        INTEGER NOT NULL CHECK (resilient_decreased_count >= 0),
    mostly_resilient_count           INTEGER NOT NULL CHECK (mostly_resilient_count >= 0),
    adjustment_unavailable_count     INTEGER NOT NULL CHECK (adjustment_unavailable_count >= 0),
    created_at                       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (universe, fr_method)
);
