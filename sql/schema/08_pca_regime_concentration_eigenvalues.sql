-- Here only DDL is written
/**
We store PCA eigenvalue rows from regime-specific return correlation matrices.

- PRIMARY KEY is (universe, regime, component), the natural identity of an
  eigenvalue row.
- This table is built by scripts/08_build_pca_regime_concentration.py.
- The PCA uses raw empirical correlation matrices for full, calm, and stress
  samples.

**/

DROP TABLE IF EXISTS pca_regime_concentration_eigenvalues;

CREATE TABLE pca_regime_concentration_eigenvalues (
    universe                             VARCHAR NOT NULL,
    regime                               VARCHAR NOT NULL CHECK (regime IN ('full', 'calm', 'stress')),
    component                            INTEGER NOT NULL CHECK (component >= 1),
    eigenvalue                           DOUBLE NOT NULL CHECK (eigenvalue >= 0),
    explained_variance_share             DOUBLE NOT NULL CHECK (explained_variance_share BETWEEN 0 AND 1),
    cumulative_explained_variance_share  DOUBLE NOT NULL CHECK (cumulative_explained_variance_share BETWEEN 0 AND 1),
    created_at                           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (universe, regime, component)
);
