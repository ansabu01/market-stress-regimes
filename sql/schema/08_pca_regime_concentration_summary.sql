-- Here only DDL is written
/**
We store PCA concentration summaries by universe and regime.

- PRIMARY KEY is (universe, regime).
- This table is built by scripts/08_build_pca_regime_concentration.py.
- effective_bets is the participation-ratio effective number of PCA directions.

**/

DROP TABLE IF EXISTS pca_regime_concentration_summary;

CREATE TABLE pca_regime_concentration_summary (
    universe         VARCHAR NOT NULL,
    regime           VARCHAR NOT NULL CHECK (regime IN ('full', 'calm', 'stress')),
    observations     INTEGER NOT NULL CHECK (observations > 0),
    assets           INTEGER NOT NULL CHECK (assets >= 2),
    stress_share     DOUBLE NOT NULL CHECK (stress_share BETWEEN 0 AND 1),
    pc1_share        DOUBLE NOT NULL CHECK (pc1_share BETWEEN 0 AND 1),
    pc2_share        DOUBLE CHECK (pc2_share BETWEEN 0 AND 1),
    top_3_share      DOUBLE NOT NULL CHECK (top_3_share BETWEEN 0 AND 1),
    top_5_share      DOUBLE NOT NULL CHECK (top_5_share BETWEEN 0 AND 1),
    effective_bets   DOUBLE NOT NULL CHECK (effective_bets > 0),
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (universe, regime)
);
