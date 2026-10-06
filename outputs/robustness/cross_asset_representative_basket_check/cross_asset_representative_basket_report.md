# Cross-Asset Representative Basket Check

This checks whether the Panel A result changes when only one ETF is kept
from each broad cross-asset bucket.

## Summary

| label | basket | n_assets | n_pairs | stress_share | avg_corr_calm | avg_corr_stress | avg_corr_diff | median_corr_diff | share_pairs_increased |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| markov_p050 | broad_4_agg_dbc | 4 | 6 | 0.453 | 0.174 | 0.262 | 0.089 | 0.139 | 0.833 |
| markov_p050 | panel_a_full | 9 | 36 | 0.481 | 0.195 | 0.170 | -0.025 | -0.024 | 0.389 |
| markov_p050 | with_gold_5_agg | 5 | 10 | 0.453 | 0.188 | 0.222 | 0.034 | 0.032 | 0.500 |
| markov_p050 | with_gold_5_hyg | 5 | 10 | 0.481 | 0.310 | 0.368 | 0.058 | 0.034 | 0.700 |
| markov_p050 | with_gold_5_shy | 5 | 10 | 0.453 | 0.162 | 0.166 | 0.004 | -0.040 | 0.400 |
| markov_p050 | with_gold_5_tlt | 5 | 10 | 0.453 | 0.150 | 0.133 | -0.017 | -0.040 | 0.300 |
| markov_p0975 | broad_4_agg_dbc | 4 | 6 | 0.189 | 0.180 | 0.291 | 0.110 | 0.145 | 0.833 |
| markov_p0975 | panel_a_full | 9 | 36 | 0.201 | 0.186 | 0.160 | -0.026 | -0.043 | 0.361 |
| markov_p0975 | with_gold_5_agg | 5 | 10 | 0.189 | 0.192 | 0.229 | 0.037 | 0.061 | 0.500 |
| markov_p0975 | with_gold_5_hyg | 5 | 10 | 0.201 | 0.345 | 0.361 | 0.015 | 0.026 | 0.600 |
| markov_p0975 | with_gold_5_shy | 5 | 10 | 0.189 | 0.167 | 0.152 | -0.015 | -0.060 | 0.300 |
| markov_p0975 | with_gold_5_tlt | 5 | 10 | 0.189 | 0.151 | 0.119 | -0.031 | -0.085 | 0.400 |
| raw_vix_drawdown | broad_4_agg_dbc | 4 | 6 | 0.161 | 0.195 | 0.288 | 0.093 | 0.134 | 0.833 |
| raw_vix_drawdown | panel_a_full | 9 | 36 | 0.166 | 0.200 | 0.139 | -0.061 | -0.052 | 0.333 |
| raw_vix_drawdown | with_gold_5_agg | 5 | 10 | 0.161 | 0.196 | 0.231 | 0.035 | 0.016 | 0.500 |
| raw_vix_drawdown | with_gold_5_hyg | 5 | 10 | 0.166 | 0.338 | 0.374 | 0.036 | 0.003 | 0.500 |
| raw_vix_drawdown | with_gold_5_shy | 5 | 10 | 0.161 | 0.180 | 0.134 | -0.046 | -0.041 | 0.300 |
| raw_vix_drawdown | with_gold_5_tlt | 5 | 10 | 0.161 | 0.150 | 0.116 | -0.035 | -0.041 | 0.300 |
| vix_only_q0975 | broad_4_agg_dbc | 4 | 6 | 0.048 | 0.203 | 0.327 | 0.124 | 0.164 | 0.833 |
| vix_only_q0975 | panel_a_full | 9 | 36 | 0.047 | 0.184 | 0.136 | -0.048 | -0.087 | 0.417 |
| vix_only_q0975 | with_gold_5_agg | 5 | 10 | 0.048 | 0.200 | 0.224 | 0.023 | 0.031 | 0.500 |
| vix_only_q0975 | with_gold_5_hyg | 5 | 10 | 0.047 | 0.343 | 0.367 | 0.024 | 0.093 | 0.600 |
| vix_only_q0975 | with_gold_5_shy | 5 | 10 | 0.048 | 0.178 | 0.088 | -0.090 | -0.137 | 0.300 |
| vix_only_q0975 | with_gold_5_tlt | 5 | 10 | 0.048 | 0.146 | 0.091 | -0.055 | -0.105 | 0.300 |

## Basket Definitions

- `panel_a_full`: SPY, SHY, TLT, AGG, HYG, GLD, DBC, USO, VNQ
- `broad_4_agg_dbc`: SPY, AGG, DBC, VNQ
- `with_gold_5_agg`: SPY, AGG, GLD, DBC, VNQ
- `with_gold_5_tlt`: SPY, TLT, GLD, DBC, VNQ
- `with_gold_5_shy`: SPY, SHY, GLD, DBC, VNQ
- `with_gold_5_hyg`: SPY, HYG, GLD, DBC, VNQ
