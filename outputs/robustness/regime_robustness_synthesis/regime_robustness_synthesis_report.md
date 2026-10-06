# Regime Robustness Synthesis

This analysis compares the same correlation calculation across several
stress definitions and summarizes which results are stable across labels.

## Universe-Level Robustness

| universe | label_name | stress_share | avg_corr_diff | median_corr_diff | share_pairs_increased | share_pairs_moderate_or_stronger |
| --- | --- | --- | --- | --- | --- | --- |
| panel_a_full | Markov P>=0.50 | 0.481 | -0.025 | -0.024 | 0.389 | 0.139 |
| panel_a_full | Markov P>=0.975 | 0.201 | -0.026 | -0.043 | 0.361 | 0.222 |
| panel_a_full | VIX+drawdown raw | 0.166 | -0.061 | -0.052 | 0.333 | 0.194 |
| panel_a_full | VIX-only q97.5 | 0.047 | -0.048 | -0.087 | 0.417 | 0.333 |
| panel_a_representative | Markov P>=0.50 | 0.453 | 0.089 | 0.139 | 0.833 | 0.500 |
| panel_a_representative | Markov P>=0.975 | 0.189 | 0.110 | 0.145 | 0.833 | 0.833 |
| panel_a_representative | VIX+drawdown raw | 0.161 | 0.093 | 0.134 | 0.833 | 0.667 |
| panel_a_representative | VIX-only q97.5 | 0.048 | 0.124 | 0.164 | 0.833 | 0.833 |
| panel_b_international_equity | Markov P>=0.50 | 0.399 | 0.133 | 0.131 | 1.000 | 0.867 |
| panel_b_international_equity | Markov P>=0.975 | 0.166 | 0.131 | 0.116 | 1.000 | 0.667 |
| panel_b_international_equity | VIX+drawdown raw | 0.145 | 0.138 | 0.125 | 1.000 | 0.867 |
| panel_b_international_equity | VIX-only q97.5 | 0.042 | 0.113 | 0.108 | 1.000 | 0.533 |

## Label Stability

| universe | label_i | label_j | spearman_delta_rank_corr | sign_agreement |
| --- | --- | --- | --- | --- |
| panel_a_full | markov_p050 | raw_vix_drawdown | 0.940 | 0.944 |
| panel_a_full | markov_p050 | markov_p0975 | 0.919 | 0.917 |
| panel_a_full | raw_vix_drawdown | vix_only_q0975 | 0.905 | 0.917 |
| panel_a_full | markov_p0975 | raw_vix_drawdown | 0.880 | 0.917 |
| panel_a_full | markov_p0975 | vix_only_q0975 | 0.868 | 0.889 |
| panel_a_full | markov_p050 | vix_only_q0975 | 0.848 | 0.917 |
| panel_a_representative | markov_p050 | raw_vix_drawdown | 0.943 | 1.000 |
| panel_a_representative | raw_vix_drawdown | vix_only_q0975 | 0.771 | 1.000 |
| panel_a_representative | markov_p050 | vix_only_q0975 | 0.543 | 1.000 |
| panel_a_representative | markov_p050 | markov_p0975 | 0.257 | 1.000 |
| panel_a_representative | markov_p0975 | vix_only_q0975 | 0.257 | 1.000 |
| panel_a_representative | markov_p0975 | raw_vix_drawdown | 0.200 | 1.000 |
| panel_b_international_equity | raw_vix_drawdown | vix_only_q0975 | 0.975 | 1.000 |
| panel_b_international_equity | markov_p0975 | raw_vix_drawdown | 0.964 | 1.000 |
| panel_b_international_equity | markov_p0975 | vix_only_q0975 | 0.961 | 1.000 |
| panel_b_international_equity | markov_p050 | vix_only_q0975 | 0.929 | 1.000 |
| panel_b_international_equity | markov_p050 | raw_vix_drawdown | 0.921 | 1.000 |
| panel_b_international_equity | markov_p050 | markov_p0975 | 0.893 | 1.000 |

## Panel B Consensus Increase Pairs

| pair | avg_delta_corr | min_delta_corr | max_delta_corr |
| --- | --- | --- | --- |
| EWU-EWJ | 0.216 | 0.189 | 0.238 |
| EWG-EWJ | 0.196 | 0.185 | 0.213 |
| SPY-EWJ | 0.191 | 0.173 | 0.208 |
| EEM-EWJ | 0.186 | 0.167 | 0.203 |
| SPY-EWU | 0.143 | 0.111 | 0.164 |
| EEM-EWU | 0.139 | 0.122 | 0.156 |
| EEM-EWG | 0.123 | 0.113 | 0.136 |
| EFA-EWJ | 0.118 | 0.103 | 0.134 |
| SPY-EWG | 0.115 | 0.095 | 0.128 |
| SPY-EEM | 0.113 | 0.089 | 0.131 |

## Panel A Pair-Type Decomposition

| label_name | pair_type | n_pairs | avg_delta_corr | share_pairs_increased |
| --- | --- | --- | --- | --- |
| Markov P>=0.50 | broad_commodity / real_estate | 1 | 0.233 | 1.000 |
| Markov P>=0.50 | oil / real_estate | 1 | 0.231 | 1.000 |
| Markov P>=0.50 | equity / real_estate | 1 | 0.210 | 1.000 |
| Markov P>=0.50 | broad_commodity / equity | 1 | 0.174 | 1.000 |
| Markov P>=0.50 | equity / oil | 1 | 0.172 | 1.000 |
| Markov P>=0.50 | aggregate_bond / broad_commodity | 1 | 0.099 | 1.000 |
| Markov P>=0.50 | aggregate_bond / oil | 1 | 0.098 | 1.000 |
| Markov P>=0.50 | broad_commodity / credit | 1 | 0.096 | 1.000 |
| Markov P>=0.50 | aggregate_bond / equity | 1 | 0.078 | 1.000 |
| Markov P>=0.50 | aggregate_bond / credit | 1 | 0.066 | 1.000 |
| Markov P>=0.50 | credit / oil | 1 | 0.054 | 1.000 |
| Markov P>=0.50 | credit / real_estate | 1 | 0.042 | 1.000 |
| Markov P>=0.50 | credit / equity | 1 | 0.026 | 1.000 |
| Markov P>=0.50 | broad_commodity / gold | 1 | 0.014 | 1.000 |
| Markov P>=0.50 | gold / oil | 1 | -0.003 | 0.000 |
| Markov P>=0.50 | gold / short_treasury | 1 | -0.011 | 0.000 |
| Markov P>=0.50 | equity / gold | 1 | -0.014 | 0.000 |
| Markov P>=0.50 | long_treasury / short_treasury | 1 | -0.019 | 0.000 |
| Markov P>=0.50 | broad_commodity / oil | 1 | -0.029 | 0.000 |
| Markov P>=0.50 | oil / short_treasury | 1 | -0.032 | 0.000 |
| Markov P>=0.50 | aggregate_bond / gold | 1 | -0.032 | 0.000 |
| Markov P>=0.50 | gold / long_treasury | 1 | -0.032 | 0.000 |
| Markov P>=0.50 | broad_commodity / short_treasury | 1 | -0.034 | 0.000 |
| Markov P>=0.50 | equity / short_treasury | 1 | -0.072 | 0.000 |
| Markov P>=0.50 | long_treasury / oil | 1 | -0.080 | 0.000 |
| Markov P>=0.50 | broad_commodity / long_treasury | 1 | -0.088 | 0.000 |
| Markov P>=0.50 | credit / gold | 1 | -0.088 | 0.000 |
| Markov P>=0.50 | gold / real_estate | 1 | -0.108 | 0.000 |
| Markov P>=0.50 | credit / short_treasury | 1 | -0.120 | 0.000 |
| Markov P>=0.50 | equity / long_treasury | 1 | -0.137 | 0.000 |
| Markov P>=0.50 | credit / long_treasury | 1 | -0.176 | 0.000 |
| Markov P>=0.50 | aggregate_bond / short_treasury | 1 | -0.214 | 0.000 |
| Markov P>=0.50 | aggregate_bond / long_treasury | 1 | -0.230 | 0.000 |
| Markov P>=0.50 | aggregate_bond / real_estate | 1 | -0.277 | 0.000 |
| Markov P>=0.50 | real_estate / short_treasury | 1 | -0.306 | 0.000 |
| Markov P>=0.50 | long_treasury / real_estate | 1 | -0.374 | 0.000 |
| VIX+drawdown raw | broad_commodity / real_estate | 1 | 0.195 | 1.000 |
| VIX+drawdown raw | oil / real_estate | 1 | 0.195 | 1.000 |
| VIX+drawdown raw | broad_commodity / equity | 1 | 0.163 | 1.000 |
| VIX+drawdown raw | equity / oil | 1 | 0.148 | 1.000 |
| VIX+drawdown raw | aggregate_bond / oil | 1 | 0.143 | 1.000 |
| VIX+drawdown raw | aggregate_bond / broad_commodity | 1 | 0.140 | 1.000 |
| VIX+drawdown raw | equity / real_estate | 1 | 0.134 | 1.000 |
| VIX+drawdown raw | broad_commodity / credit | 1 | 0.092 | 1.000 |
| VIX+drawdown raw | aggregate_bond / credit | 1 | 0.091 | 1.000 |
| VIX+drawdown raw | aggregate_bond / equity | 1 | 0.071 | 1.000 |
| VIX+drawdown raw | credit / oil | 1 | 0.039 | 1.000 |
| VIX+drawdown raw | credit / equity | 1 | 0.019 | 1.000 |
| VIX+drawdown raw | broad_commodity / gold | 1 | -0.013 | 0.000 |
| VIX+drawdown raw | credit / real_estate | 1 | -0.027 | 0.000 |
| VIX+drawdown raw | gold / oil | 1 | -0.031 | 0.000 |
| VIX+drawdown raw | long_treasury / short_treasury | 1 | -0.036 | 0.000 |
| VIX+drawdown raw | equity / gold | 1 | -0.040 | 0.000 |
| VIX+drawdown raw | gold / real_estate | 1 | -0.043 | 0.000 |
| VIX+drawdown raw | broad_commodity / oil | 1 | -0.062 | 0.000 |
| VIX+drawdown raw | long_treasury / oil | 1 | -0.062 | 0.000 |
| VIX+drawdown raw | gold / long_treasury | 1 | -0.078 | 0.000 |
| VIX+drawdown raw | oil / short_treasury | 1 | -0.096 | 0.000 |
| VIX+drawdown raw | broad_commodity / long_treasury | 1 | -0.102 | 0.000 |
| VIX+drawdown raw | aggregate_bond / gold | 1 | -0.104 | 0.000 |
| VIX+drawdown raw | credit / gold | 1 | -0.120 | 0.000 |
| VIX+drawdown raw | aggregate_bond / real_estate | 1 | -0.162 | 0.000 |
| VIX+drawdown raw | broad_commodity / short_treasury | 1 | -0.162 | 0.000 |
| VIX+drawdown raw | gold / short_treasury | 1 | -0.208 | 0.000 |
| VIX+drawdown raw | equity / short_treasury | 1 | -0.212 | 0.000 |
| VIX+drawdown raw | equity / long_treasury | 1 | -0.223 | 0.000 |
| VIX+drawdown raw | credit / long_treasury | 1 | -0.245 | 0.000 |
| VIX+drawdown raw | credit / short_treasury | 1 | -0.262 | 0.000 |
| VIX+drawdown raw | real_estate / short_treasury | 1 | -0.283 | 0.000 |
| VIX+drawdown raw | aggregate_bond / long_treasury | 1 | -0.322 | 0.000 |
| VIX+drawdown raw | long_treasury / real_estate | 1 | -0.341 | 0.000 |
| VIX+drawdown raw | aggregate_bond / short_treasury | 1 | -0.390 | 0.000 |
| VIX-only q97.5 | oil / real_estate | 1 | 0.289 | 1.000 |
| VIX-only q97.5 | equity / oil | 1 | 0.241 | 1.000 |
| VIX-only q97.5 | credit / oil | 1 | 0.207 | 1.000 |
| VIX-only q97.5 | aggregate_bond / broad_commodity | 1 | 0.206 | 1.000 |
| VIX-only q97.5 | aggregate_bond / oil | 1 | 0.202 | 1.000 |
| VIX-only q97.5 | broad_commodity / equity | 1 | 0.198 | 1.000 |
| VIX-only q97.5 | broad_commodity / real_estate | 1 | 0.193 | 1.000 |
| VIX-only q97.5 | broad_commodity / credit | 1 | 0.190 | 1.000 |
| VIX-only q97.5 | aggregate_bond / credit | 1 | 0.165 | 1.000 |
| VIX-only q97.5 | aggregate_bond / equity | 1 | 0.138 | 1.000 |
| VIX-only q97.5 | equity / real_estate | 1 | 0.117 | 1.000 |
| VIX-only q97.5 | credit / equity | 1 | 0.104 | 1.000 |
| VIX-only q97.5 | credit / real_estate | 1 | 0.083 | 1.000 |
| VIX-only q97.5 | long_treasury / short_treasury | 1 | 0.032 | 1.000 |
| VIX-only q97.5 | broad_commodity / oil | 1 | 0.009 | 1.000 |
| VIX-only q97.5 | gold / long_treasury | 1 | -0.014 | 0.000 |
| VIX-only q97.5 | aggregate_bond / gold | 1 | -0.039 | 0.000 |
| VIX-only q97.5 | aggregate_bond / real_estate | 1 | -0.087 | 0.000 |
| VIX-only q97.5 | long_treasury / oil | 1 | -0.088 | 0.000 |
| VIX-only q97.5 | broad_commodity / long_treasury | 1 | -0.098 | 0.000 |
| VIX-only q97.5 | gold / oil | 1 | -0.105 | 0.000 |
| VIX-only q97.5 | broad_commodity / gold | 1 | -0.108 | 0.000 |
| VIX-only q97.5 | gold / short_treasury | 1 | -0.129 | 0.000 |
| VIX-only q97.5 | equity / gold | 1 | -0.144 | 0.000 |
| VIX-only q97.5 | credit / gold | 1 | -0.181 | 0.000 |
| VIX-only q97.5 | equity / long_treasury | 1 | -0.189 | 0.000 |
| VIX-only q97.5 | gold / real_estate | 1 | -0.213 | 0.000 |
| VIX-only q97.5 | credit / long_treasury | 1 | -0.235 | 0.000 |
| VIX-only q97.5 | real_estate / short_treasury | 1 | -0.238 | 0.000 |
| VIX-only q97.5 | oil / short_treasury | 1 | -0.245 | 0.000 |
| VIX-only q97.5 | equity / short_treasury | 1 | -0.267 | 0.000 |
| VIX-only q97.5 | long_treasury / real_estate | 1 | -0.277 | 0.000 |
| VIX-only q97.5 | broad_commodity / short_treasury | 1 | -0.305 | 0.000 |
| VIX-only q97.5 | aggregate_bond / long_treasury | 1 | -0.340 | 0.000 |
| VIX-only q97.5 | credit / short_treasury | 1 | -0.362 | 0.000 |
| VIX-only q97.5 | aggregate_bond / short_treasury | 1 | -0.432 | 0.000 |

## Suggested Wording

The international-equity correlation increase is robust across materially different stress definitions. The cross-asset result is more composition-dependent: risky-asset and real-estate/commodity links often increase, while Treasury and safe-haven relationships offset the full Panel A average.
