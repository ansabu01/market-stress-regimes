"""
Markov-switching stress regime for SPY -- the single source of truth.

-------------------------------------
We label every period (a month, or a week for the robustness check) as either
"calm" or "stress":

1. Take daily SPY adjusted-close prices.
2. Keep the last trading day of each period and compute its log return.
3. Fit a two-state Markov-switching model. Each state has its own average
   return and its own variance, and the model gives us, for every period, the
   probability of being in each state.
4. The "stress" state is simply the one with the higher variance.
5. A period is labelled "stress" when its stress probability is >= 0.5 (we also
   keep a stricter 0.75 label as a robustness check).

The same functions are used for both frequencies; only the names in the
``MONTHLY`` and ``WEEKLY`` settings differ. The monthly regime is the official
one (built by scripts/05_00_build_markov_switching_monthly.py); the weekly regime
is a robustness check (scripts/05_01_build_weekly_markov_switching.py).
"""

from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression


# Model settings (the same for monthly and weekly).
N_STATES = 2                    # the hidden states
STRESS_CUTOFF = 0.50            # a period is "stress" when P(stress) >= this
HIGH_CONFIDENCE_CUTOFF = 0.75   # stricter label, kept only for robustness


@dataclass
class RegimeConfig:
    """The handful of names that differ between the monthly and weekly regimes."""

    model_name: str          # e.g. "markov_switching_monthly_spy"
    model_frequency: str     # label stored in the tables: "M" or "W"
    pandas_freq: str         # how pandas groups days into periods: "M" or "W-FRI"
    period_column: str       # date column in the output table: "month_end" / "week_end"
    log_return_column: str   # e.g. "spy_monthly_log_return"
    return_pct_column: str   # e.g. "spy_monthly_return_pct" (the return in %)
    regime_table: str        # output table with one row per period
    summary_table: str       # output table with one row describing the model
    comparison_table: str    # output table comparing against the rule-based labels


MONTHLY = RegimeConfig(
    model_name="markov_switching_monthly_spy",
    model_frequency="M",
    pandas_freq="M",
    period_column="month_end",
    log_return_column="spy_monthly_log_return",
    return_pct_column="spy_monthly_return_pct",
    regime_table="markov_regime_monthly",
    summary_table="markov_model_summary",
    comparison_table="markov_monthly_comparison",
)

WEEKLY = RegimeConfig(
    model_name="markov_switching_weekly_spy",
    model_frequency="W",
    pandas_freq="W-FRI",
    period_column="week_end",
    log_return_column="spy_weekly_log_return",
    return_pct_column="spy_weekly_return_pct",
    regime_table="markov_regime_weekly",
    summary_table="markov_weekly_model_summary",
    comparison_table="markov_weekly_comparison",
)


# ---------------------------------------------------------------------------
# 1. Prices -> period returns
# ---------------------------------------------------------------------------

def load_spy_prices(con) -> pd.DataFrame: 
    """Read daily SPY adjusted-close prices from the database, oldest first."""
    spy = con.execute(
        """
        SELECT date, price AS adj_close
        FROM asset_prices
        WHERE ticker = 'SPY' AND price_source = 'adj_close'
        ORDER BY date
        """
    ).fetchdf()

    if spy.empty:
        raise RuntimeError("No SPY adj_close prices found. Run scripts/02 first.")

    spy["date"] = pd.to_datetime(spy["date"])
    
    return spy # gives the adj_close returns from SPY as a dataframe as output


def build_periodic_spy_returns(spy_prices, cfg=MONTHLY) -> pd.DataFrame:
    """Turn daily prices into one log return per period (last trading day)."""
    prices = spy_prices.sort_values("date").copy()
    prices["period"] = prices["date"].dt.to_period(cfg.pandas_freq)
    # Keep the last trading day in each period and take log returns between them.
    last_day = prices.groupby("period").tail(1).sort_values("date").reset_index(drop=True) # makes the PERIOD-YEAR the INDEX
    last_day[cfg.log_return_column] = np.log(last_day["adj_close"]).diff() # calculates the LOG returns month over month
    last_day[cfg.return_pct_column] = 100 * last_day[cfg.log_return_column]

    # The first period has no previous period to compare to, so drop it.
    last_day = last_day.dropna(subset=[cfg.log_return_column])
    last_day = last_day.rename(columns={"date": cfg.period_column})
    return last_day[[cfg.period_column, cfg.log_return_column, cfg.return_pct_column]].reset_index(drop=True)


def build_monthly_spy_returns(spy_prices) -> pd.DataFrame:
    """Monthly SPY log returns (used by the official regime)."""
    return build_periodic_spy_returns(spy_prices, MONTHLY) # Calls the above function


# ---------------------------------------------------------------------------
# 2. Fit the model and find the stress state
# ---------------------------------------------------------------------------

def fit_markov_switching_model(returns, cfg=MONTHLY):
    """Fit the two-state model. Each state has its own mean and variance."""
    model = MarkovRegression(
        returns[cfg.return_pct_column],
        k_regimes=N_STATES,
        trend="c",
        switching_trend=True,      # each state has its own average return (Can be debated but according to literature the best state)
        switching_variance=True,   # each state has its own variance
    )
    return model.fit(disp=False)


def extract_state_variances(result):
    """The two fitted variances, as {0: variance_of_state_0, 1: ...}."""
    return {0: result.params["sigma2[0]"], 1: result.params["sigma2[1]"]}


def identify_stress_state(state_variances):
    """Stress is the state with the higher variance."""
    return 0 if state_variances[0] > state_variances[1] else 1 # Note: We define the hidden state with the higher variance the stress regime


def sanitize_probability_array(values):
    """Clip model-implied probabilities to the valid [0, 1] range."""
    return np.clip(np.asarray(values, dtype=float), 0.0, 1.0)


# ---------------------------------------------------------------------------
# 3. Build the output tables (one row per period, plus a model summary)
# ---------------------------------------------------------------------------

def build_markov_regime_table(returns, result, stress_state, cfg=MONTHLY):
    """One row per period: the return, the stress probability, and the labels."""
    # smoothed_marginal_probabilities has one column per state (0 and 1).
    smoothed = result.smoothed_marginal_probabilities 
    prob_stress = smoothed[stress_state].to_numpy() 

    table = returns.copy()
    table["ms_prob_state_0"] = sanitize_probability_array(smoothed[0].to_numpy())
    table["ms_prob_state_1"] = sanitize_probability_array(smoothed[1].to_numpy())
    table["ms_prob_stress"] = sanitize_probability_array(prob_stress)
    table["ms_stress_50"] = prob_stress >= STRESS_CUTOFF # This is the main analysis
    table["ms_stress_75"] = prob_stress >= HIGH_CONFIDENCE_CUTOFF # rather used as robustness, not supported since its arbitrary
    table["calm_state"] = 1 - stress_state
    table["stress_state"] = stress_state
    table["model_name"] = cfg.model_name
    table["model_frequency"] = cfg.model_frequency
    table[cfg.period_column] = pd.to_datetime(table[cfg.period_column]).dt.date

    # Put the columns in the order the database table expects.
    return table[[
        cfg.period_column,
        cfg.log_return_column,
        cfg.return_pct_column,
        "ms_prob_state_0",
        "ms_prob_state_1",
        "calm_state",
        "stress_state",
        "ms_prob_stress",
        "ms_stress_50",
        "ms_stress_75",
        "model_name",
        "model_frequency",
    ]]


### AI supported function.
def build_markov_model_summary(result, returns, stress_state, cfg=MONTHLY):
    """One row describing the fitted model (variances, sample, fit quality)."""
    variances = extract_state_variances(result)
    return pd.DataFrame([{
        "model_name": cfg.model_name,
        "model_frequency": cfg.model_frequency,
        "sample_start": returns[cfg.period_column].min().date(),
        "sample_end": returns[cfg.period_column].max().date(),
        "n_observations": len(returns),
        "k_regimes": N_STATES,
        "trend_spec": "c",
        "switching_variance": True,
        "state_0_variance": variances[0],
        "state_1_variance": variances[1],
        "calm_state": 1 - stress_state,
        "stress_state": stress_state,
        "log_likelihood": result.llf,
        "aic": result.aic,
        "bic": result.bic,
    }])


def write_markov_outputs(con, regime_df, summary_df, cfg=MONTHLY):
    """Insert the per-period rows and the one-row summary into their tables."""
    regime_cols = ", ".join(regime_df.columns) # WE need sql column format for inserting
    con.execute(
        f"INSERT OR IGNORE INTO {cfg.regime_table} ({regime_cols}) " # only select columns for inserting
        f"SELECT {regime_cols} FROM regime_df" # insert
    )

    summary_cols = ", ".join(summary_df.columns) # here too 
    con.execute(
        f"INSERT OR IGNORE INTO {cfg.summary_table} ({summary_cols}) " # same here
        f"SELECT {summary_cols} FROM summary_df"
    )


# ---------------------------------------------------------------------------
# 4. Robustness checks (agreement measured with Cohen's kappa)
# ---------------------------------------------------------------------------

def cohens_kappa(observed_agreement, share_a, share_b):
    """Agreement corrected for chance (1 = perfect, 0 = no better than chance).

    Useful here because stress is rare, so two labels can agree most of the
    time just by both saying "calm".
    """
    chance = share_a * share_b + (1 - share_a) * (1 - share_b)
    return (observed_agreement - chance) / (1 - chance)


def build_markov_vs_defined_comparison(con, cfg=MONTHLY):
    """Compare the Markov stress label against the rule-based VIX + drawdown labels.

    The rule-based labels (from scripts/04) are daily; the Markov label is per
    period, so we attach each day to its period's Markov label and compare.
    Returns one row per (rule label, Markov threshold) and stores them in
    cfg.comparison_table. Returns None if the inputs are not available yet.
    """
    tables = set(con.execute("SHOW TABLES").fetchdf()["name"])
    if "regime_labels" not in tables or cfg.regime_table not in tables:
        return None

    rule = con.execute(
        "SELECT date, stress_raw, stress_smooth_21d FROM regime_labels ORDER BY date"
    ).fetchdf()
    markov = con.execute(
        f"SELECT {cfg.period_column} AS period_end, ms_stress_50, ms_stress_75 "
        f"FROM {cfg.regime_table}"
    ).fetchdf()

    # Match every daily rule-based row to the Markov label of its period.
    rule["period"] = pd.to_datetime(rule["date"]).dt.to_period(cfg.pandas_freq)
    markov["period"] = pd.to_datetime(markov["period_end"]).dt.to_period(cfg.pandas_freq)
    merged = rule.merge(markov, on="period", how="inner")

    rows = []
    for rule_label in ["stress_raw", "stress_smooth_21d"]:
        for markov_label in ["ms_stress_50", "ms_stress_75"]:
            a = merged[rule_label].astype(int).to_numpy()
            b = merged[markov_label].astype(int).to_numpy()
            agreement = (a == b).mean()
            rows.append({
                "model_frequency": cfg.model_frequency,
                "defined_label": rule_label,
                "markov_label": markov_label,
                "common_days": len(merged),
                "defined_stress_share": a.mean(),
                "markov_stress_share": b.mean(),
                "agreement_rate": agreement,
                "cohen_kappa": cohens_kappa(agreement, a.mean(), b.mean()),
                "both_stress_days": int(((a == 1) & (b == 1)).sum()),
                "markov_only_stress_days": int(((a == 0) & (b == 1)).sum()),
                "defined_only_stress_days": int(((a == 1) & (b == 0)).sum()),
                "both_calm_days": int(((a == 0) & (b == 0)).sum()),
            })

    summary = pd.DataFrame(rows)
    con.execute(f"CREATE OR REPLACE TABLE {cfg.comparison_table} AS SELECT * FROM summary")
    return summary


def build_markov_frequency_comparison(con):
    """Does the weekly regime agree with the monthly one? (frequency robustness)

    We put the monthly stress label onto each week (by calendar month) and
    compare week by week. Stored in markov_weekly_vs_monthly_comparison.
    """
    tables = set(con.execute("SHOW TABLES").fetchdf()["name"])
    if WEEKLY.regime_table not in tables or MONTHLY.regime_table not in tables:
        return None

    weekly = con.execute(
        f"SELECT {WEEKLY.period_column} AS week_end, ms_stress_50, ms_stress_75 "
        f"FROM {WEEKLY.regime_table}"
    ).fetchdf()
    monthly = con.execute(
        f"SELECT {MONTHLY.period_column} AS month_end, ms_stress_50, ms_stress_75 "
        f"FROM {MONTHLY.regime_table}"
    ).fetchdf()

    weekly["month"] = pd.to_datetime(weekly["week_end"]).dt.to_period("M")
    monthly["month"] = pd.to_datetime(monthly["month_end"]).dt.to_period("M")
    merged = weekly.merge(monthly, on="month", how="inner", suffixes=("_weekly", "_monthly"))

    rows = []
    for threshold in ["ms_stress_50", "ms_stress_75"]:
        w = merged[f"{threshold}_weekly"].astype(int).to_numpy()
        m = merged[f"{threshold}_monthly"].astype(int).to_numpy()
        agreement = (w == m).mean()
        rows.append({
            "markov_label": threshold,
            "common_weeks": len(merged),
            "weekly_stress_share": w.mean(),
            "monthly_stress_share": m.mean(),
            "agreement_rate": agreement,
            "cohen_kappa": cohens_kappa(agreement, w.mean(), m.mean()),
            "both_stress_weeks": int(((w == 1) & (m == 1)).sum()),
            "weekly_only_stress_weeks": int(((w == 1) & (m == 0)).sum()),
            "monthly_only_stress_weeks": int(((w == 0) & (m == 1)).sum()),
            "both_calm_weeks": int(((w == 0) & (m == 0)).sum()),
        })

    summary = pd.DataFrame(rows)
    con.execute("CREATE OR REPLACE TABLE markov_weekly_vs_monthly_comparison AS SELECT * FROM summary")
    return summary
