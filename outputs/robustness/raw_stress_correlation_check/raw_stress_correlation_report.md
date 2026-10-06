# Raw Stress Label Correlation Check

Label source: `regime_labels.stress_raw` only.

The script rebuilds daily ETF log returns from `asset_prices`, joins the raw
VIX-plus-drawdown stress label by date, and computes calm/stress Pearson
correlations on strict complete-case samples.

## Summary

| universe | n_assets | n_pairs | n_calm_days | n_stress_days | stress_share | avg_corr_calm | avg_corr_stress | avg_corr_diff | median_corr_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| etf_assets | 14 | 91 | 3928 | 783 | 0.166 | 0.300 | 0.296 | -0.004 | 0.046 |
| panel_a_cross_asset | 9 | 36 | 3928 | 783 | 0.166 | 0.200 | 0.139 | -0.061 | -0.052 |
| panel_b_international_equity | 6 | 15 | 4889 | 826 | 0.145 | 0.752 | 0.890 | 0.138 | 0.125 |

## Interpretation Counts

| universe | interpretation | n_pairs | share |
| --- | --- | --- | --- |
| etf_assets | Correlation decreased | 40 | 0.43956043956043955 |
| etf_assets | Moderate breakdown | 30 | 0.32967032967032966 |
| etf_assets | Small increase | 21 | 0.23076923076923078 |
| panel_a_cross_asset | Correlation decreased | 24 | 0.6666666666666666 |
| panel_a_cross_asset | Moderate breakdown | 7 | 0.19444444444444445 |
| panel_a_cross_asset | Small increase | 5 | 0.1388888888888889 |
| panel_b_international_equity | Moderate breakdown | 13 | 0.8666666666666667 |
| panel_b_international_equity | Small increase | 2 | 0.13333333333333333 |
