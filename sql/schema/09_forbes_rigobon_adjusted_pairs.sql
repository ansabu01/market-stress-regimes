-- Here only DDL is written
/**
We store Forbes-Rigobon adjusted pair correlations under two adjustment
methods: market_spy (SPY variance shock for SPY pairs only) and pair_max
(larger shock of the two assets for every pair).

- PRIMARY KEY is (universe, fr_method, asset_i, asset_j).
- source_asset identifies SPY or the higher-variance pair member.
- corr_calm, corr_stress, and delta_corr are the raw values loaded from the
  correlation_pairs table; they are not recalculated by the FR script.
- This table is built by scripts/09_build_forbes_rigobon_adjusted_correlations.py.
- When stress variance is higher, the FR adjustment shrinks |corr| toward
  zero. All adjusted correlations remain in [-1, 1].

**/

DROP TABLE IF EXISTS forbes_rigobon_adjusted_pairs;

CREATE TABLE forbes_rigobon_adjusted_pairs (
    universe              VARCHAR NOT NULL,
    correlation_method    VARCHAR NOT NULL,
    fr_method             VARCHAR NOT NULL CHECK (fr_method IN ('market_spy', 'pair_max')),
    source_asset          VARCHAR,
    asset_i               VARCHAR NOT NULL,
    asset_j               VARCHAR NOT NULL,
    corr_calm             DOUBLE NOT NULL CHECK (corr_calm BETWEEN -1 AND 1),
    corr_stress           DOUBLE NOT NULL CHECK (corr_stress BETWEEN -1 AND 1),
    delta_corr            DOUBLE NOT NULL CHECK (delta_corr BETWEEN -2 AND 2),
    fr_delta_asset_i      DOUBLE CHECK (fr_delta_asset_i >= 0),
    fr_delta_asset_j      DOUBLE CHECK (fr_delta_asset_j >= 0),
    fr_delta_spy          DOUBLE CHECK (fr_delta_spy >= 0),
    fr_delta_used         DOUBLE CHECK (fr_delta_used >= 0),
    corr_stress_adjusted  DOUBLE CHECK (corr_stress_adjusted BETWEEN -1 AND 1),
    delta_corr_adjusted   DOUBLE CHECK (delta_corr_adjusted BETWEEN -2 AND 2),
    interpretation        VARCHAR NOT NULL,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (universe, fr_method, asset_i, asset_j)
);
