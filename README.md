# Market-Stress Regimes and Diversification Breakdown

This project examines whether diversification weakens during market stress by comparing regime-dependent correlations and risk concentration across a multi-asset ETF universe.

- **Pipeline:** [`scripts/run_all.py`](scripts/run_all.py)
- **Dashboard:** [`app/streamlit_app.py`](app/streamlit_app.py)
- **Report:** [`report/report.pdf`](report/report.pdf)
- **Presentation:** [`outputs/presentation/final_presentation_draft.pptx`](outputs/presentation/final_presentation_draft.pptx)

## Overview

Daily ETF returns from 2000 to 2025 are classified into calm and stress regimes using a two-state Markov-switching model fitted to monthly SPY returns. The analysis compares regime-conditional correlations, bootstrap inference, principal-component concentration, and Forbes--Rigobon volatility-adjusted correlations. A Streamlit dashboard provides interactive access to the principal results and exploratory portfolio diagnostics.

## Key Findings

- Diversification weakens most clearly within international equities during stress.
- Both the international-equity and cross-asset panels become more concentrated, with a stronger dominant principal component and fewer effective independent directions.
- After the Forbes--Rigobon adjustment, no pair retains a robust correlation breakdown, indicating that the raw increases are largely associated with higher stress-period volatility.
- Sovereign bonds and gold remain comparatively resilient diversifiers, although the stock--Treasury relationship is less stable across stress episodes.

## Repository Structure

```text
app/          Streamlit dashboard and dashboard-ready data
notebooks/    Analysis and visualization notebooks
outputs/      Generated figures, tables, and presentation materials
report/       Final report PDF and LaTeX source
scripts/      Numbered pipeline entry points
sql/schema/   DuckDB table definitions
src/          Reusable data, regime, and analysis code
tests/        Automated analytical checks
```

## Installation

Python 3.11 or newer is required.

```bash
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Usage

Run the project smoke test:

```bash
python scripts/00_smoke_test.py
```

Run the complete data and analysis pipeline:

```bash
python scripts/run_all.py
```

Export the dashboard-ready data and launch the application:

```bash
python scripts/10_export_dashboard_data.py
python -m streamlit run app/streamlit_app.py
```

Run the automated checks:

```bash
python -m pytest
```

## Data and Reproducibility

Market prices and VIX observations are downloaded from Yahoo Finance through `yfinance`. The pipeline builds the local DuckDB database, assigns point-in-time regime labels, and regenerates the analytical tables. The dashboard reads the precomputed Parquet files in `app/data/` and does not refit the models or modify the official results.

## Contributors

- Andrea Saliola Bucelli
- Florian Säwert
- [Timo Baumgartner](https://github.com/01baumgartner41-ux)

## License

The project code is released under the [MIT License](LICENSE). The license does not cover third-party data, institutional branding, or externally licensed materials.
