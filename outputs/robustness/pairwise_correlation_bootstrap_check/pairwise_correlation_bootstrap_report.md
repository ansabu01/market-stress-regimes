# Pairwise Correlation Bootstrap Check

Bootstrap: 2,000 circular moving-block resamples, block length 21 trading days.
Calm and stress observations are resampled separately within each universe/label.

## Universe-Level Average Delta

| universe | label_name | stress_share | avg_delta_corr | avg_ci_low | avg_ci_high | valid_rise_pairs | valid_fall_pairs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| panel_a_full | Markov P>=0.50 | 0.481 | -0.025 | -0.067 | 0.018 | 6 | 8 |
| panel_a_full | Markov P>=0.975 | 0.201 | -0.026 | -0.074 | 0.025 | 6 | 4 |
| panel_a_full | VIX+drawdown raw | 0.166 | -0.061 | -0.114 | -0.008 | 5 | 12 |
| panel_a_full | VIX-only q97.5 | 0.047 | -0.048 | -0.116 | 0.032 | 5 | 10 |
| panel_a_representative | Markov P>=0.50 | 0.453 | 0.089 | 0.016 | 0.150 | 3 | 1 |
| panel_a_representative | Markov P>=0.975 | 0.189 | 0.110 | 0.028 | 0.173 | 3 | 0 |
| panel_a_representative | VIX+drawdown raw | 0.161 | 0.093 | -0.013 | 0.164 | 3 | 1 |
| panel_a_representative | VIX-only q97.5 | 0.048 | 0.124 | -0.023 | 0.215 | 1 | 0 |
| panel_b_international_equity | Markov P>=0.50 | 0.399 | 0.133 | 0.095 | 0.164 | 15 | 0 |
| panel_b_international_equity | Markov P>=0.975 | 0.166 | 0.131 | 0.093 | 0.159 | 15 | 0 |
| panel_b_international_equity | VIX+drawdown raw | 0.145 | 0.138 | 0.098 | 0.165 | 15 | 0 |
| panel_b_international_equity | VIX-only q97.5 | 0.042 | 0.113 | 0.051 | 0.154 | 15 | 0 |

## Panel B Pairwise Example: Markov P>=0.50

| pair | delta_corr | ci_low | ci_high | q_boot_bh |
| --- | --- | --- | --- | --- |
| EWU-EWJ | 0.210 | 0.141 | 0.262 | 0.001 |
| EWG-EWJ | 0.186 | 0.127 | 0.233 | 0.001 |
| SPY-EWJ | 0.173 | 0.113 | 0.221 | 0.001 |
| EEM-EWJ | 0.172 | 0.107 | 0.223 | 0.001 |
| SPY-EWU | 0.164 | 0.111 | 0.204 | 0.001 |
| EEM-EWU | 0.156 | 0.109 | 0.197 | 0.001 |
| EEM-EWG | 0.136 | 0.090 | 0.176 | 0.001 |
| SPY-EEM | 0.131 | 0.087 | 0.168 | 0.001 |
| SPY-EWG | 0.128 | 0.083 | 0.165 | 0.001 |
| EFA-EEM | 0.111 | 0.081 | 0.137 | 0.001 |
| SPY-EFA | 0.109 | 0.073 | 0.137 | 0.001 |
| EWG-EWU | 0.104 | 0.069 | 0.135 | 0.001 |
| EFA-EWJ | 0.103 | 0.062 | 0.133 | 0.001 |
| EFA-EWU | 0.064 | 0.042 | 0.085 | 0.001 |
| EFA-EWG | 0.054 | 0.037 | 0.070 | 0.001 |

## Suggested Wording

Bootstrap intervals confirm that the international-equity correlation increase is not only directionally robust across labels, but also statistically stable at the pair level. Cross-asset results remain mixed: some risky-asset links have positive intervals, while Treasury and safe-haven pairs often have negative intervals.
