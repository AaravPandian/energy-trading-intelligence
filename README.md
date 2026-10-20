# 🛢️ Energy Trading Intelligence & Risk Dashboard

[![Python tests](https://img.shields.io/badge/tests-14%20passed-0f766e)](#automated-tests) ![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB) ![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B) ![Data](https://img.shields.io/badge/data-U.S.%20EIA%20monthly-orange)

**A beginner-level, end-to-end energy market analytics project using Python, Pandas, SQLite, Streamlit, Plotly and Excel.**

**Portfolio status:** Complete sample project with reproducible historical data, formula-based Excel model, working SQL queries, and automated CI. The Excel workbook recalculates formulas when opened in Microsoft Excel or a compatible spreadsheet editor. The Streamlit interface is intended to be run locally or deployed; it has not been visually smoke-tested in this execution environment.

The app examines **Brent and WTI crude-oil prices**, calculates historical volatility, studies the Brent–WTI price spread and shows how hypothetical oil-price shocks can affect a physical buyer or seller. It then generates **rule-based commercial review points**, not speculative trade recommendations.

> **Data cut:** January 2021–August 2026, monthly averages, sourced from the U.S. Energy Information Administration (EIA). This is a frozen, offline dataset. The app does **not** show today's crude price or trading quotes.

## Business questions

1. How have Brent and WTI monthly prices moved over time?
2. When was monthly-price volatility highest, and how is risk changing?
3. How wide is the Brent–WTI spread, and which periods stand out?
4. How does a ±5%, ±10% or ±20% hypothetical price move change an energy buyer's cost or producer's revenue?
5. How does a simplified fixed-price coverage assumption change the scenario exposure?
6. What commercially sensible follow-up actions might procurement or treasury teams review?

## Features

| Component | What it does | Tools |
|---|---|---|
| Market monitor | Price trends, latest prices, month-on-month changes, Brent–WTI spread | Pandas, Plotly, Streamlit |
| Risk analysis | 6-month rolling annualised volatility, worst and 5th-percentile historical monthly changes | Pandas, NumPy, Plotly |
| Scenario lab | Buyer vs seller, exposed barrels, hypothetical shock, fixed-price share | Python, Streamlit |
| SQL explorer | Six business questions against a real SQLite database | SQL, sqlite3 |
| Excel model | Editable scenario assumptions, monthly-price history, dashboard / scenario grid | Excel |
| QA | Dataset tests, price checks, scenario arithmetic, SQL checks | pytest, GitHub Actions |

## Architecture

```text
EIA monthly Brent & WTI data (frozen, sourced CSV)
                    |
             Python / Pandas
                    |
         Return & volatility metrics
                    |
        +-----------+------------+
        |           |            |
     SQLite     Streamlit       Excel
    6 queries   Plotly UI    Scenario model
```

## Quick start — macOS / Linux

Requirements: **Python 3.11 or newer**, internet once to install Python packages, and a terminal. **No paid Bloomberg account, API key, Power BI or SQL server** is required.

```bash
# 1. In Terminal, move into the extracted project folder.
cd energy-trading-intelligence

# 2. Create an isolated Python environment.
python3 -m venv .venv
source .venv/bin/activate

# 3. Install packages.
python -m pip install -r requirements.txt

# 4. Launch the interactive dashboard.
python -m streamlit run app.py
```

Open the local URL shown in Terminal (usually **http://localhost:8501**). The app reads the bundled data automatically; **you do not need to build the database first**.

Optional: generate the SQLite database on disk, or run the tests:

```bash
python -m scripts.build_database
python -m scripts.build_excel  # Rebuild the formula-driven Excel workbook
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

### Windows equivalents

Use `python -m venv .venv`, activate with `.venv\Scripts\activate`, then use the same installation/run commands.

## Data dictionary

File: `data/eia_monthly_spot_prices.csv`

| Column | Meaning |
|---|---|
| `month` | First day of the represented **calendar month** (YYYY-MM-01, a period label) |
| `benchmark` | `Brent` or `WTI` |
| `price_usd_bbl` | EIA average spot price during the month, U.S. dollars per barrel |
| `source_url` | Direct link to the relevant EIA published series |

**136 records** = 68 monthly averages × 2 benchmarks, January 2021 through August 2026. The data are **real published historical EIA values**, not synthetic prices. Source pages:

- [EIA: Europe Brent Spot Price FOB (monthly)](https://www.eia.gov/dnav/pet/hist/rbrtem.htm)
- [EIA: Cushing, OK WTI Spot Price FOB (monthly)](https://www.eia.gov/dnav/pet/hist/rwtcm.htm)

Transcribed on **20 October 2026**, latest included month **August 2026**. EIA data can subsequently be revised. `scripts/prepare_sample_data.py` records the fixed figures used for this reproducible educational snapshot. *2026 is an incomplete year: Jan–Aug only.*

## Methodology

**Monthly percentage change**

```text
Monthly change = Current month's average price / Previous month's average price − 1
```

**6-month rolling annualised volatility** (historical description, not a risk forecast)

```text
Annualised volatility = sample_std_dev(last 6 monthly changes) × sqrt(12)
```

The first monthly price has no return. The sixth return first appears with the seventh price observation; before that there are too few observations for the 6-month rolling-volatility measure. Since the underlying prices are **monthly averages**, monthly changes here are **not close-to-close investment returns** and must not be presented as a genuine trading P&L distribution.

**Brent–WTI spread**

```text
Spread ($/barrel) = Brent monthly average − WTI monthly average
```

**Scenario cash-flow effect**: For a **buyer**, a +10% price shock is a cost increase (negative effect on cash flow); for a **seller**, the same shock is a positive revenue change. The *fixed-price share* assumes that a given share has no change from the baseline price. It is **not** a hedge model or a claim about futures hedge effectiveness, margin, options, premiums, basis risk or taxes.

A **5th-percentile monthly change** is shown as a descriptive lower-tail historical statistic; it is **not** a validated Value at Risk estimate.

## Typical illustrative commercial finding

**Example:** An energy buyer with a 10,000-barrel planned purchase at **$80/bbl** faces an **$80,000 cost increase** if oil goes up 10%. Under a *simplified* assumption that 50% of the volume was already fixed at the original price, the change is **$40,000**. These are hypothetical calculations, **not claims of realised savings or an executable hedge**.

**What a commercial analyst might suggest:** Refresh procurement budgets, consider shorter quote-validity periods when historical volatility is elevated, and ask treasury to review exposures and approved hedging policies. The recommendations are threshold-based educational prompts and **do not predict prices**.

## Folder structure

```text
energy-trading-intelligence/
├── app.py                         # Streamlit dashboard, 5 tabs
├── data/
│   └── eia_monthly_spot_prices.csv # Real EIA monthly averages
├── excel/
│   └── Energy_Risk_Analysis.xlsx   # Editable Excel model
├── sql/
│   ├── 01_yearly_prices.sql
│   ├── 02_widest_spreads.sql
│   ├── 03_biggest_price_moves.sql
│   ├── 04_volatility_watch.sql
│   ├── 05_latest_risk_snapshot.sql
│   └── 06_spread_regimes.sql
├── src/
│   ├── analytics.py                # Returns, spread, vol, risk summaries
│   ├── database.py                 # SQLite loader and query execution
│   ├── scenarios.py                # Cash-flow stress-test engine
│   └── recommendations.py          # Rule-based commercial commentary
├── scripts/
│   ├── build_database.py
│   ├── build_excel.py         # Build Excel workbook offline (Python stdlib)
│   └── prepare_sample_data.py      # Rebuild reproducible CSV snapshot
├── tests/test_project.py
├── docs/
│   ├── learning_path.md
│   ├── interview_guide.md
│   └── data_methodology.md
├── .github/workflows/python-tests.yml
├── requirements.txt
├── requirements-dev.txt
└── LICENSE
```

## Automated tests

Fourteen `pytest` checks cover dataset coverage, official source observations, returns/annualisation, spread arithmetic, buyer/seller impacts, fixed-share stress reduction, invalid parameters, scenario grid, SQL integrity, risk statistics, commentary and the Excel workbook structure. GitHub Actions runs the tests on commits and pull requests.

## What I learned / how to explain it in interviews

This portfolio project demonstrates **data sourcing, cleaning and validation, historical risk analytics, SQL reporting, commercial scenario analysis and end-user visualisation**. It is a deliberately **beginner-friendly analytics case study**, not a live trading platform. Read [`docs/interview_guide.md`](docs/interview_guide.md) before discussing methodology with recruiters.

### Suggested CV bullet

> Built a Python/SQL energy-market analytics dashboard using 136 U.S. EIA monthly Brent/WTI observations, with Pandas volatility measures, Plotly visualisations, commercial price-shock scenarios and an Excel analysis model; added automated tests and GitHub CI.

## Deploy free on Streamlit Community Cloud

1. Push this repository to GitHub.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), choose **Create app** and connect your repo.
3. Set the main file to `app.py` and deploy.
4. The included CSV makes deployment **API-key free**. Data stays frozen until you deliberately update the source snapshot.

## Limitations / disclaimer

A monthly-average historical dataset cannot support real-time execution, tradable hedge pricing, a calibrated VaR model, transaction-cost estimates, or physical oil procurement decisions alone. No predictive accuracy or simulated trading returns are claimed. All scenario parameters are illustrative. This project is intended for education and portfolio demonstration only.

## Licence

MIT (software). EIA is credited as the source of the public historical data; maintain attribution when reusing it.

## Upload this repository to GitHub (Mac)

Unzip the downloaded project, open Terminal in the extracted folder, then run:

```bash
git init
git add .
git commit -m "Build energy market and commercial risk dashboard"
git branch -M main
gh auth status   # If you are signed in, continue. Otherwise: gh auth login
gh repo create energy-trading-intelligence --public --source=. --remote=origin --push
```

The `.gitignore` protects local virtual environments, cache files and SQLite databases.
Don't upload API credentials or private trading data. The source prices are historical and public.

If the GitHub repository already exists, replace the final `gh repo create` line with:

```bash
git remote add origin https://github.com/YOUR_USERNAME/energy-trading-intelligence.git
git push -u origin main
```
