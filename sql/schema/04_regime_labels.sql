-- Here only DDL is written
/**
We store the preprocessed data from the 

- PRIMARY KEY will be the date (Datetime)



**/

DROP TABLE IF EXISTS regime_labels;

CREATE TABLE regime_labels (
    date DATE PRIMARY KEY,
    vix_close_adj DOUBLE,
    vix_q75_252 DOUBLE,
    spx_close_adj DOUBLE,
    spx_rollmax_252 DOUBLE,
    spx_drawdown DOUBLE,
    stress_raw INTEGER,
    stress_smooth_21d INTEGER,
    regime VARCHAR
);