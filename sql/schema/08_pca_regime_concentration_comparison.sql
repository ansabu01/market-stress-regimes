-- Here only DDL is written
/**
We store the calm-vs-stress PCA concentration comparison by universe.

- PRIMARY KEY is universe.
- This table is built by scripts/08_build_pca_regime_concentration.py.
- more_concentrated_in_stress is true when stress raises PC1 share and lowers
  the effective number of bets.

**/

DROP TABLE IF EXISTS pca_regime_concentration_comparison;

CREATE TABLE pca_regime_concentration_comparison (
    universe                              VARCHAR PRIMARY KEY,
    calm_pc1_share                        DOUBLE NOT NULL CHECK (calm_pc1_share BETWEEN 0 AND 1),
    stress_pc1_share                      DOUBLE NOT NULL CHECK (stress_pc1_share BETWEEN 0 AND 1),
    stress_minus_calm_pc1_share           DOUBLE NOT NULL,
    calm_effective_bets                   DOUBLE NOT NULL CHECK (calm_effective_bets > 0),
    stress_effective_bets                 DOUBLE NOT NULL CHECK (stress_effective_bets > 0),
    stress_minus_calm_effective_bets      DOUBLE NOT NULL,
    more_concentrated_in_stress           BOOLEAN NOT NULL,
    created_at                            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
