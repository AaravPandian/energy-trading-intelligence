# Recruiter & interview guide

## The 30-second description

"I built an interactive energy analytics dashboard using genuine U.S. EIA monthly Brent and WTI price histories. I used Pandas to calculate benchmark spreads, monthly changes and rolling annualised volatility, SQLite for six commercial reporting questions, and Streamlit/Plotly for interactive charts. I also created a buyer/seller scenario tool to show how oil-price shocks can affect a planned physical exposure. It is an educational decision-support prototype, not a production trading system."

## Five questions you should be ready for

**1. Why Brent and WTI?** They are internationally used oil-price reference benchmarks, and their differential can matter for commercial price references and regional exposures. The spread is not an arbitrage profit.

**2. Where does the data come from?** Official EIA monthly spot-price history, January 2021–August 2026. Each month represents a price average, NOT a daily or end-month tradeable price.

**3. How did you measure volatility?** Standard deviation of the previous six month-to-month changes in monthly *average* price, multiplied by √12 for annualisation. Sample volatility describes dispersion; it does not forecast future movement.

**4. How does the hedge slider work?** The exposed percentage of a purchase or sale that remains unfixed responds to the chosen price shock. It assumes perfect fixing and ignores implementation costs, basis and margin. Real hedge models require futures curves and counterparty exposure data.

**5. What action could a firm take from your work?** Monitor benchmark exposures, refresh price-sensitive budgets, consider approval of fixed-price supply terms, and escalate unusually high historical variability to procurement/treasury. It should supplement company-specific data, not trigger autonomous trade decisions.

## Behavioural framing

- **Problem:** Energy price swings complicate procurement budgets and commercial revenue planning.
- **Approach:** Source historical prices → validate → calculate risk indicators → build scenario analyses → communicate practical, qualified next steps.
- **Result:** A reproducible dashboard + SQL reporting + Excel model suitable for discussion and further development.
- **Next step:** Add a governed daily market data feed, supply contract detail, forward curves, backtesting and controls.

## Never claim

- It streams live oil trading prices.
- You built futures or options valuation, predictive AI or regulatory VaR.
- The results prove profitable trades or realised savings.
- The project uses hundreds of thousands of observations: it uses **136** price records.

## Two legitimate CV points

1. Built an interactive Python, Pandas, Plotly and Streamlit energy dashboard using 136 historical Brent/WTI price records from U.S. EIA, including benchmark spreads and six-month rolling annualised volatility.
2. Implemented SQL reporting and a buyer/seller price-shock calculator with an editable fixed-price exposure assumption, supported by automated pytest checks and an Excel model.
