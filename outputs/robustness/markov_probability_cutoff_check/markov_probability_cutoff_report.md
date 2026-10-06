# Markov Probability Cutoff Correlation Check

Label source: `markov_regime_monthly.ms_prob_stress`.

For each cutoff, daily ETF returns inherit the monthly Markov stress
probability and are classified as stress only when the probability is at
least the cutoff.

## Summary

| cutoff | universe | n_stress_months | stress_month_share | n_stress_days | stress_day_share | avg_corr_calm | avg_corr_stress | avg_corr_diff | median_corr_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.500 | etf_assets | 108 | 0.480 | 2268 | 0.481 | 0.282 | 0.311 | 0.029 | 0.050 |
| 0.500 | panel_a_cross_asset | 108 | 0.480 | 2268 | 0.481 | 0.195 | 0.170 | -0.025 | -0.024 |
| 0.500 | panel_b_international_equity | 109 | 0.399 | 2279 | 0.399 | 0.731 | 0.865 | 0.133 | 0.131 |
| 0.750 | etf_assets | 86 | 0.382 | 1802 | 0.383 | 0.287 | 0.309 | 0.022 | 0.028 |
| 0.750 | panel_a_cross_asset | 86 | 0.382 | 1802 | 0.383 | 0.194 | 0.166 | -0.028 | -0.033 |
| 0.750 | panel_b_international_equity | 86 | 0.315 | 1802 | 0.315 | 0.741 | 0.871 | 0.130 | 0.127 |
| 0.900 | etf_assets | 66 | 0.293 | 1386 | 0.294 | 0.289 | 0.308 | 0.019 | 0.035 |
| 0.900 | panel_a_cross_asset | 66 | 0.293 | 1386 | 0.294 | 0.187 | 0.164 | -0.023 | -0.034 |
| 0.900 | panel_b_international_equity | 66 | 0.242 | 1386 | 0.243 | 0.752 | 0.878 | 0.126 | 0.114 |
| 0.975 | etf_assets | 45 | 0.200 | 947 | 0.201 | 0.289 | 0.309 | 0.020 | 0.043 |
| 0.975 | panel_a_cross_asset | 45 | 0.200 | 947 | 0.201 | 0.186 | 0.160 | -0.026 | -0.043 |
| 0.975 | panel_b_international_equity | 45 | 0.165 | 947 | 0.166 | 0.757 | 0.888 | 0.131 | 0.116 |

## Pair Interpretation Counts

| cutoff | universe | interpretation | n_pairs | share |
| --- | --- | --- | --- | --- |
| 0.5 | etf_assets | Correlation decreased | 38 | 0.4175824175824176 |
| 0.5 | etf_assets | Moderate breakdown | 31 | 0.34065934065934067 |
| 0.5 | etf_assets | Small increase | 22 | 0.24175824175824176 |
| 0.5 | panel_a_cross_asset | Correlation decreased | 22 | 0.6111111111111112 |
| 0.5 | panel_a_cross_asset | Small increase | 9 | 0.25 |
| 0.5 | panel_a_cross_asset | Moderate breakdown | 5 | 0.1388888888888889 |
| 0.5 | panel_b_international_equity | Moderate breakdown | 13 | 0.8666666666666667 |
| 0.5 | panel_b_international_equity | Small increase | 2 | 0.13333333333333333 |
| 0.75 | etf_assets | Correlation decreased | 37 | 0.4065934065934066 |
| 0.75 | etf_assets | Moderate breakdown | 36 | 0.3956043956043956 |
| 0.75 | etf_assets | Small increase | 18 | 0.1978021978021978 |
| 0.75 | panel_a_cross_asset | Correlation decreased | 20 | 0.5555555555555556 |
| 0.75 | panel_a_cross_asset | Moderate breakdown | 9 | 0.25 |
| 0.75 | panel_a_cross_asset | Small increase | 7 | 0.19444444444444445 |
| 0.75 | panel_b_international_equity | Moderate breakdown | 12 | 0.8 |
| 0.75 | panel_b_international_equity | Small increase | 3 | 0.2 |
| 0.9 | etf_assets | Correlation decreased | 38 | 0.4175824175824176 |
| 0.9 | etf_assets | Small increase | 27 | 0.2967032967032967 |
| 0.9 | etf_assets | Moderate breakdown | 26 | 0.2857142857142857 |
| 0.9 | panel_a_cross_asset | Correlation decreased | 23 | 0.6388888888888888 |
| 0.9 | panel_a_cross_asset | Moderate breakdown | 8 | 0.2222222222222222 |
| 0.9 | panel_a_cross_asset | Small increase | 5 | 0.1388888888888889 |
| 0.9 | panel_b_international_equity | Moderate breakdown | 10 | 0.6666666666666666 |
| 0.9 | panel_b_international_equity | Small increase | 5 | 0.3333333333333333 |
| 0.975 | etf_assets | Correlation decreased | 38 | 0.4175824175824176 |
| 0.975 | etf_assets | Moderate breakdown | 29 | 0.31868131868131866 |
| 0.975 | etf_assets | Small increase | 24 | 0.26373626373626374 |
| 0.975 | panel_a_cross_asset | Correlation decreased | 23 | 0.6388888888888888 |
| 0.975 | panel_a_cross_asset | Moderate breakdown | 8 | 0.2222222222222222 |
| 0.975 | panel_a_cross_asset | Small increase | 5 | 0.1388888888888889 |
| 0.975 | panel_b_international_equity | Moderate breakdown | 10 | 0.6666666666666666 |
| 0.975 | panel_b_international_equity | Small increase | 5 | 0.3333333333333333 |
