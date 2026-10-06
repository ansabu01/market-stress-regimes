# Speaker notes — "Safe Until It Isn't" (TUM Data Science in Finance seminar)

Target: 12–15 minutes, 12 main slides + 2 backup. The same notes are embedded in the
`.pptx` (Presenter View). Numbers are taken verbatim from `report/report.pdf`
and the pipeline outputs; nothing is new to this deck.

---

## Slide 1 — Title / research question
- One-line pitch: portfolios that look diversified in calm markets can lose that protection exactly in stress; we measure how much, and whether the loss is structural.
- Full pipeline: DuckDB + Python, two ETF panels, a Markov-switching stress regime, three measurement layers (correlations, PCA concentration, Forbes–Rigobon).
- Everything is reproducible: `scripts/run_all.py` + notebooks 01–06 regenerate every figure and table.
- 12–15 minutes; questions at the end.

## Slide 2 — Motivation
- Growth of $100 from each panel's common start: every drawdown hits nearly all lines together.
- The classic complaint: "correlations go to one in a crisis." We test how literally that is true, pair by pair.
- Design idea: don't average over calm and crisis — condition the whole dependence structure on a stress regime and compare.
- Research question on record: does diversification survive when it is needed most, and is the deterioration structural or mechanical?

## Slide 3 — Data
- Panel A spans the classic diversification menu: equity, short/long Treasuries, aggregate + high-yield credit, gold, commodities, oil, listed real estate.
- Panel B asks a different question: does geographic equity diversification survive stress?
- US-listed ETFs mean synchronous NYSE closes — no asynchronicity bias in daily correlations.
- HYG (Apr 2007) anchors the balanced window; all universes share the same 4,711 days and calm/stress mix (2,443 / 2,268).
- Returns are heavily non-Gaussian (excess kurtosis up to 55) — motivates regime-based analysis.

## Slide 4 — Regime identification
- Two latent states with own mean and variance: calm μ +1.44% / σ 2.38% per month; stress μ −0.14% / σ 5.65%.
- Stress = the higher-variance state, ex post, smoothed probabilities, 0.5 maximum-probability rule.
- Both states persistent (p_CC = 0.941, p_SS = 0.939) → regimes last ≈ 17 months; "stress" is a high-volatility era, not a crash day.
- BIC-preferred vs. variance-only / mean-only / three-state; robust to 0.75 threshold, weekly frequency, optimizer initialization.
- Validation: agrees with an independent VIX + drawdown rule well beyond chance (Cohen's κ ≈ 0.5 weekly).

## Slide 5 — Returns → stress probabilities (mechanism)
- Suggested caption: "The model evaluates returns under calm and stress state distributions and combines this with regime persistence. The fitted transition matrix is fixed, while the probability of being in the stress state changes over time."
- May 2017: +1.4% is typical calm behaviour → P(stress) 0.01 → Calm.
- Apr 2012: −0.7% is ambiguous on its own — persistence from neighbouring stress months tips it to P(stress) 0.53 → Stress. This is the pedagogical core: the label is not a per-month threshold on returns.
- Oct 2008: −18.1% is essentially impossible under the calm density → P(stress) 1.00.
- Animated version (GIF/HTML in `outputs/figures/`) can replace this figure for the live talk.

## Slide 6 — Raw regime-conditional correlations
- Same balanced days; Pearson correlations computed separately on calm and stress days.
- Panel B: all 15 pairs above the diagonal — uniform tightening, average 0.74 → 0.87.
- Panel A: flat average hides a reshuffle — risk-on pairs (SPY/DBC/USO with VNQ) tighten while Treasury and gold pairs decouple further (TLT–VNQ falls by 0.37).
- 61% of Panel A pairs see their correlation FALL in stress — the opposite of the textbook breakdown.
- Raw descriptive numbers; the next two slides ask what survives inference and the volatility correction.

## Slide 7 — Bootstrap inference
- Circular block bootstrap: whole cross-sectional rows resampled in 21-day chronological blocks together with their regime labels (B = 2,000).
- Panel B: +0.124, CI [+0.084, +0.157], p < 0.001, all 15 pairs FDR-significant — the one unambiguous universe-level result.
- Panel A and combined averages are NOT distinguishable from zero (p = 0.27 / 0.16), but the pair-level reshuffle is real: 6 significant increases vs. 8 decreases.
- Methodological point: respecting serial dependence removes roughly a third of the "discoveries" a naive i.i.d. Fisher-z test would claim (73 → 50 after FDR).
- Inference is conditional on the estimated regime labels (stated limitation).

## Slide 8 — PCA concentration
- Eigendecomposition of the regime-conditional correlation matrices; effective bets = participation ratio.
- Every universe concentrates in stress: PC1 share up, effective bets down.
- Panel B nearly degenerate in stress: PC1 = 89% of variance, 1.26 effective bets across six markets.
- Panel A subtler: flat average correlation, yet concentration rises — the reshuffle loads risk-on and safe-haven blocks onto the SAME leading axis (N_eff 4.52 → 4.33).
- Portfolio reading: about one-fifth of an independent bet lost cross-asset; almost everything lost in international equity.

## Slide 9 — Forbes–Rigobon
- Forbes–Rigobon (2002): measured correlation rises mechanically when common-factor variance rises, even with an unchanged relationship.
- Figure: circles = raw stress-minus-calm change, diamonds = adjusted; every raw "breakdown" slides back below the 0.10 threshold.
- Zero robust breakdowns in every universe under both variants → interdependence, not contagion.
- The asymmetry is the practical finding: fragility concentrates in equities; 19 of 28 non-SPY cross-asset pairs are genuinely resilient (Treasuries, gold).
- Caveat: exact only under a single-factor, variance-only regime shift.

## Slide 10 — Stress-episode heterogeneity (descriptive nuance)
- The Markov label says WHEN markets are stressed, not WHICH macro shock causes it.
- Split by broad era: the whole duration sleeve flips sign in 2022–23 (SPY–TLT −0.48/−0.45 → +0.10; TLT–AGG rises to 0.91) — consistent with inflation-driven stock–bond comovement (Campbell–Pflueger–Viceira 2020).
- Gold is the exception: SPY–GLD within [+0.01, +0.15] in every episode — episode-robust.
- ~76% of stress days predate 2022, so the pooled Treasury-hedge estimate is dominated by deflationary-type episodes.
- Framing: average stress-regime property, not an unconditional hedge guarantee. Descriptive only — no formal inference on the split.

## Slide 11 — Streamlit dashboard (supplement)
- Position as supplement/demo, not a result: same DuckDB, read-only, exploring the published numbers only.
- Two interactions worth demoing live: the regime-threshold slider and the pair drill-down with rolling correlation (the 2022 SPY–TLT flip is visible to the naked eye).
- Deployment plan: Streamlit Community Cloud; the 25 MB DuckDB ships with the repo.
- Be explicit: screenshots are TODO — the deck contains no mocked dashboard output.

## Slide 12 — Conclusion
- Three sentences: stress concentrates risk in realized terms; the rise is volatility-driven interdependence, not structural contagion; the exposures that keep diversifying are genuinely different assets — sovereign duration and gold — not more equities.
- Keep claims diagnostic, not prescriptive: we evaluate diversification under regimes; we do not propose an allocation rule.
- The 2022 qualification is the honest limit: the regime label does not identify the macro shock behind the stress.
- Close with reproducibility: one command rebuilds the database, figures, and report tables.

## Backup A — Regime timeline
- SPY (log scale) with stress shading; smoothed P(stress) with both thresholds; agreement swim-lanes.
- Monthly Markov, weekly Markov, and the rule-based VIX+drawdown label identify the same episodes (κ ≈ 0.5).
- Stress covers 47% of months — long high-volatility eras, not crash days.

## Backup B — Pipeline flow
- Use if asked "how exactly is the label built?".
- Transition matrix is FIXED after fitting; only state probabilities are time-varying.
- Downstream box = why the regime matters: correlations, PCA, Forbes–Rigobon all condition on these labels.
- Animated walk-through: `outputs/figures/markov_probability_animation.gif` / `.html`.
