"""
Run the full data pipeline in order.

Run from the project root:

    python scripts/run_all.py

The runner stops at the first failing script.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PIPELINE_STEPS = [
    ("00_smoke_test.py", "Check imports and database path"),
    ("01_init_database.py", "Initialise database setup"),
    ("02_fetch_market_prices.py", "Fetch ETF and VIX prices"),
    ("04_build_regime_labels.py", "Build rule-based daily regime labels"),
    ("05_00_build_markov_switching_monthly.py", "Build monthly Markov-switching SPY regime"),
    (
        "05_01_build_weekly_markov_switching.py",
        "Build weekly Markov-switching SPY regime (robustness)",
    ),
    (
        "06_assign_monthly_markov_regimes_to_daily_returns.py",
        "Assign monthly Markov labels to daily returns",
    ),
    ("07_build_regime_correlations.py", "Build regime-conditional correlation tables"),
    ("08_build_pca_regime_concentration.py", "Build PCA regime concentration analysis"),
    (
        "09_build_forbes_rigobon_adjusted_correlations.py",
        "Build Forbes-Rigobon adjusted correlation tables",
    ),
]


def run_step(script_name: str, description: str) -> None:
    script_path = PROJECT_ROOT / "scripts" / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Missing pipeline script: {script_path}")

    print()
    print("=" * 80)
    print(f"Running {script_name}: {description}")
    print("=" * 80)

    start_time = time.perf_counter()
    command = [sys.executable, str(script_path)]
    try:
        subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print()
        print("=" * 80)
        print(f"Pipeline stopped: {script_name} failed with exit code {exc.returncode}")
        print(f"Command: {' '.join(command)}")
        print("=" * 80)
        raise SystemExit(exc.returncode) from None

    elapsed = time.perf_counter() - start_time
    print(f"Finished {script_name} in {elapsed:.1f}s")


def main() -> None:
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Python: {sys.executable}")

    start_time = time.perf_counter()
    for script_name, description in PIPELINE_STEPS:
        run_step(script_name, description)

    elapsed = time.perf_counter() - start_time
    print()
    print("=" * 80)
    print(f"Pipeline completed successfully in {elapsed:.1f}s")
    print("=" * 80)


if __name__ == "__main__":
    main()
