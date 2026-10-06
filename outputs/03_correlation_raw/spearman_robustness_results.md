# Spearman Robustness Results

Same balanced-window sample as the Pearson regime-correlation tables:
`n_calm_days = 2443`, `n_stress_days = 2268`.

## Core Summary

| universe | method | n_assets | n_pairs | avg_corr_calm | avg_corr_stress | avg_corr_diff | median_corr_calm | median_corr_stress | median_corr_diff |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| panel_a_cross_asset | spearman | 9 | 36 | 0.1847 | 0.1712 | -0.0135 | 0.1334 | 0.1375 | -0.0214 |
| panel_b_international_equity | spearman | 6 | 15 | 0.7142 | 0.8069 | 0.0927 | 0.6952 | 0.7940 | 0.0979 |
| etf_assets | spearman | 14 | 91 | 0.2688 | 0.2905 | 0.0217 | 0.2136 | 0.3323 | 0.0272 |

## Distribution Checks

| universe | p10_corr_calm | p10_corr_stress | p10_corr_diff | p90_corr_calm | p90_corr_stress | p90_corr_diff | min_corr_calm | min_corr_stress | max_corr_calm | max_corr_stress |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| panel_a_cross_asset | -0.1451 | -0.2132 | -0.1129 | 0.6293 | 0.6791 | 0.1632 | -0.2237 | -0.3185 | 0.8891 | 0.8796 |
| panel_b_international_equity | 0.5910 | 0.7210 | 0.0553 | 0.8457 | 0.8972 | 0.1287 | 0.5827 | 0.7092 | 0.8864 | 0.9333 |
| etf_assets | -0.1224 | -0.2244 | -0.1286 | 0.7100 | 0.7927 | 0.1757 | -0.2237 | -0.3185 | 0.8891 | 0.9333 |

## Pearson vs Spearman Delta Check

| universe | pearson_avg_corr_diff | spearman_avg_corr_diff | pearson_median_corr_diff | spearman_median_corr_diff |
|---|---:|---:|---:|---:|
| panel_a_cross_asset | -0.0246 | -0.0135 | -0.0243 | -0.0214 |
| panel_b_international_equity | 0.1245 | 0.0927 | 0.1247 | 0.0979 |
| etf_assets | 0.0291 | 0.0217 | 0.0499 | 0.0272 |
