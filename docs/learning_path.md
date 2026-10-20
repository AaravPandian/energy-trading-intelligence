# Beginner learning path: understand the project after uploading

You can upload this whole repository now. To confidently explain it later, do these seven short lessons in order. No prior energy-trading experience is required.

## 1 — Understand the business (60–90 minutes)

Learn: What is a barrel of oil? What are Brent and WTI benchmark spot prices? What does a refinery or airline buy, and what does a producer sell? Why does price volatility matter for budgets?

Explain in one sentence: *"My app helps a commercial energy team see how historical price changes affect buying or selling decisions."*

## 2 — Learn the CSV and Pandas (90–120 minutes)

Open `data/eia_monthly_spot_prices.csv`, then `src/analytics.py`.

Try `pd.read_csv`, `head`, `groupby`, `sort_values`, `pivot`, and `pct_change`. Print the price in June 2022 for Brent and WTI and confirm they are **$122.71** and **$114.84**.

## 3 — Learn basic statistics (90–120 minutes)

Calculate monthly price changes by dividing the current monthly average by the previous one and subtracting one. Learn standard deviation. Study `rolling(6).std()` and why monthly-to-annual scaling is `sqrt(12)`.

**Important:** This is NOT daily volatility or true close-to-close trading returns.

## 4 — Learn SQL (2–3 hours)

Run `python -m scripts.build_database`. Open the `.sqlite` file with a SQLite browser, or use the built-in SQL Explorer tab. Learn `SELECT`, `WHERE`, `GROUP BY`, `AVG`, `CASE`, `JOIN` and `LAG`. Run the six queries and explain each in plain English.

## 5 — Learn scenario maths (60–90 minutes)

Open `src/scenarios.py`. If the buyer purchases 10,000 barrels at $80, that is an $800,000 baseline outflow. A 10% increase means another $80,000 of cost. With 50% fixed-price coverage *in this simplistic example*, the increase is $40,000. Change each input and predict the output before running code.

## 6 — Understand Streamlit and Plotly (2–4 hours)

Read `app.py`. Locate `st.metric`, `st.tabs`, `st.slider`, `st.plotly_chart`, `px.line`, and `px.bar`. Change the title, add a metric, and compare buyer/seller positions.

## 7 — Understand Excel + publish (1–2 hours)

Open `excel/Energy_Risk_Analysis.xlsx`. Change the blue inputs on **Assumptions**. Verify Risk Summary and Scenario Grid update. Change the shock from +15% to −10% and explain the revised cash flow.

Then run `python -m pytest -q`. Commit your own change to GitHub. Document it in the README.

## Suggested upgrades after the beginner version

- Implement a live EIA API pull (with explicit API keys and error handling).
- Add an energy procurement budget against a user-defined contract quantity.
- Compare annualised volatility from *daily* data (correctly using `sqrt(252)`).
- Learn futures term structure before adding hedging logic.
- Add data-refresh timestamps and historical revision checks.

**Interview checkpoint:** Be able to explain every number on the dashboard, particularly the 6-month volatility, spread, fixed-price proxy and lack of forecasting.
