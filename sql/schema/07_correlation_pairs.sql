-- Here only DDL is written
/**
We store the long pairwise correlation table: one row per (universe, method,
regime, asset pair).

- PRIMARY KEY is (universe, method, regime, asset_i, asset_j), the natural
  identity of a pair row.
- This table is built by scripts/07_build_regime_correlations.py.
- calm/stress rows hold plain correlations in [-1, 1]; stress_minus_calm rows
  hold differences in [-2, 2]. The CHECK below enforces both ranges.

**/

DROP TABLE IF EXISTS correlation_pairs;

CREATE TABLE correlation_pairs (
    universe     VARCHAR NOT NULL,
    method       VARCHAR NOT NULL,
    regime       VARCHAR NOT NULL CHECK (regime IN ('calm', 'stress', 'stress_minus_calm')),
    asset_i      VARCHAR NOT NULL,
    asset_j      VARCHAR NOT NULL,
    correlation  DOUBLE NOT NULL CHECK (
        CASE
            WHEN regime = 'stress_minus_calm' THEN correlation BETWEEN -2 AND 2
            ELSE correlation BETWEEN -1 AND 1
        END
    ),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (universe, method, regime, asset_i, asset_j)
);
