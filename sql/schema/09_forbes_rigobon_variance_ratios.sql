-- Here only DDL is written
/**
We store stress-vs-calm return variance ratios per asset; fr_delta is the
Forbes-Rigobon variance shock max(variance_ratio - 1, 0).

- PRIMARY KEY is (universe, asset).
- This table is built by scripts/09_build_forbes_rigobon_adjusted_correlations.py.
- variance columns may be NULL if an asset lacks valid calm/stress samples.
- fr_delta is clipped at zero (classical, one-sided Forbes-Rigobon); the signed
  raw shock is always recoverable as variance_ratio - 1.

**/

DROP TABLE IF EXISTS forbes_rigobon_variance_ratios;

CREATE TABLE forbes_rigobon_variance_ratios (
    universe         VARCHAR NOT NULL,
    asset            VARCHAR NOT NULL,
    calm_variance    DOUBLE CHECK (calm_variance > 0),
    stress_variance  DOUBLE CHECK (stress_variance >= 0),
    variance_ratio   DOUBLE CHECK (variance_ratio >= 0),
    fr_delta         DOUBLE CHECK (fr_delta >= 0),
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (universe, asset)
);
