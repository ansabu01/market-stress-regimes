# VIX-Only High-Cutoff Correlation Check

Label source: `vix_quotes` close only.

Stress is defined as VIX above a trailing 252-trading-day percentile.
There is no drawdown condition and no Markov label.

## Summary

| vix_quantile | universe | n_stress_days | stress_day_share | avg_vix_stress | avg_corr_calm | avg_corr_stress | avg_corr_diff | median_corr_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.900 | etf_assets | 591 | 0.125 | 30.506 | 0.300 | 0.294 | -0.006 | 0.066 |
| 0.900 | panel_a_cross_asset | 591 | 0.125 | 30.506 | 0.192 | 0.138 | -0.054 | -0.048 |
| 0.900 | panel_b_international_equity | 638 | 0.112 | 29.532 | 0.766 | 0.892 | 0.126 | 0.116 |
| 0.950 | etf_assets | 356 | 0.076 | 33.769 | 0.295 | 0.305 | 0.009 | 0.084 |
| 0.950 | panel_a_cross_asset | 356 | 0.076 | 33.769 | 0.185 | 0.143 | -0.042 | -0.062 |
| 0.950 | panel_b_international_equity | 388 | 0.068 | 32.458 | 0.775 | 0.900 | 0.125 | 0.118 |
| 0.975 | etf_assets | 220 | 0.047 | 36.227 | 0.298 | 0.299 | 0.001 | 0.088 |
| 0.975 | panel_a_cross_asset | 220 | 0.047 | 36.227 | 0.184 | 0.136 | -0.048 | -0.087 |
| 0.975 | panel_b_international_equity | 242 | 0.042 | 34.599 | 0.789 | 0.902 | 0.113 | 0.108 |
| 0.990 | etf_assets | 119 | 0.025 | 38.808 | 0.298 | 0.285 | -0.013 | 0.043 |
| 0.990 | panel_a_cross_asset | 119 | 0.025 | 38.808 | 0.180 | 0.123 | -0.057 | -0.087 |
| 0.990 | panel_b_international_equity | 132 | 0.023 | 36.827 | 0.796 | 0.903 | 0.106 | 0.100 |

## Pair Interpretation Counts

| vix_quantile | universe | interpretation | n_pairs | share |
| --- | --- | --- | --- | --- |
| 0.9 | etf_assets | Correlation decreased | 37 | 0.4065934065934066 |
| 0.9 | etf_assets | Moderate breakdown | 33 | 0.3626373626373626 |
| 0.9 | etf_assets | Small increase | 21 | 0.23076923076923078 |
| 0.9 | panel_a_cross_asset | Correlation decreased | 22 | 0.6111111111111112 |
| 0.9 | panel_a_cross_asset | Moderate breakdown | 9 | 0.25 |
| 0.9 | panel_a_cross_asset | Small increase | 5 | 0.1388888888888889 |
| 0.9 | panel_b_international_equity | Moderate breakdown | 11 | 0.7333333333333333 |
| 0.9 | panel_b_international_equity | Small increase | 4 | 0.26666666666666666 |
| 0.95 | etf_assets | Moderate breakdown | 38 | 0.4175824175824176 |
| 0.95 | etf_assets | Correlation decreased | 37 | 0.4065934065934066 |
| 0.95 | etf_assets | Small increase | 15 | 0.16483516483516483 |
| 0.95 | etf_assets | Strong breakdown | 1 | 0.01098901098901099 |
| 0.95 | panel_a_cross_asset | Correlation decreased | 22 | 0.6111111111111112 |
| 0.95 | panel_a_cross_asset | Moderate breakdown | 10 | 0.2777777777777778 |
| 0.95 | panel_a_cross_asset | Small increase | 3 | 0.08333333333333333 |
| 0.95 | panel_a_cross_asset | Strong breakdown | 1 | 0.027777777777777776 |
| 0.95 | panel_b_international_equity | Moderate breakdown | 10 | 0.6666666666666666 |
| 0.95 | panel_b_international_equity | Small increase | 5 | 0.3333333333333333 |
| 0.975 | etf_assets | Moderate breakdown | 40 | 0.43956043956043955 |
| 0.975 | etf_assets | Correlation decreased | 36 | 0.3956043956043956 |
| 0.975 | etf_assets | Small increase | 14 | 0.15384615384615385 |
| 0.975 | etf_assets | Strong breakdown | 1 | 0.01098901098901099 |
| 0.975 | panel_a_cross_asset | Correlation decreased | 21 | 0.5833333333333334 |
| 0.975 | panel_a_cross_asset | Moderate breakdown | 11 | 0.3055555555555556 |
| 0.975 | panel_a_cross_asset | Small increase | 3 | 0.08333333333333333 |
| 0.975 | panel_a_cross_asset | Strong breakdown | 1 | 0.027777777777777776 |
| 0.975 | panel_b_international_equity | Moderate breakdown | 8 | 0.5333333333333333 |
| 0.975 | panel_b_international_equity | Small increase | 7 | 0.4666666666666667 |
| 0.99 | etf_assets | Correlation decreased | 36 | 0.3956043956043956 |
| 0.99 | etf_assets | Moderate breakdown | 29 | 0.31868131868131866 |
| 0.99 | etf_assets | Small increase | 20 | 0.21978021978021978 |
| 0.99 | etf_assets | Strong breakdown | 6 | 0.06593406593406594 |
| 0.99 | panel_a_cross_asset | Correlation decreased | 19 | 0.5277777777777778 |
| 0.99 | panel_a_cross_asset | Small increase | 8 | 0.2222222222222222 |
| 0.99 | panel_a_cross_asset | Moderate breakdown | 6 | 0.16666666666666666 |
| 0.99 | panel_a_cross_asset | Strong breakdown | 3 | 0.08333333333333333 |
| 0.99 | panel_b_international_equity | Small increase | 8 | 0.5333333333333333 |
| 0.99 | panel_b_international_equity | Moderate breakdown | 7 | 0.4666666666666667 |
