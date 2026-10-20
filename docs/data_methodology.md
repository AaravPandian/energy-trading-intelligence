# Data provenance, statistical methodology and constraints

## Historical data / exact provenance

- Brent: U.S. Energy Information Administration, monthly Europe Brent Spot Price FOB ($/bbl): https://www.eia.gov/dnav/pet/hist/rbrtem.htm
- WTI: U.S. Energy Information Administration, monthly Cushing, OK WTI Spot Price FOB ($/bbl): https://www.eia.gov/dnav/pet/hist/rwtcm.htm
- Snapshot copied: 20 October 2026.
- Last included complete historical month: August 2026.
- Time horizon: January 2021–August 2026 inclusive (68 months × 2 series).
- Prices use the EIA values as displayed, rounded to two decimal places.
- No missing month/benchmark values within this frozen dataset.
- The string YYYY-MM-01 is a calendar-month label, **not** a claim that the price was traded on the first day.

## Calculation equations

1. Monthly reference-price change: `P_t / P_(t-1) − 1`.
2. Six-change rolling volatility: `STDEV.S(last six monthly reference-price changes) × √12`.
3. Spread: `Brent monthly average − WTI monthly average`.
4. Lower-tail observation: 5th sample percentile of historical monthly reference-price changes for that benchmark.
5. Under a hypothetical shock `s`, buyer cost exposure variation is `−P × barrels × s`, seller revenue variation `+P × barrels × s`.
6. Under a fixed-price coverage proxy `h`, remaining variation is `variation × (1 − h)`.

## Interpreting annualisation

The `√12` transformation is the common scaling convention for monthly changes, but correlations between months and nonstationarity can make it misleading. Prices are averages, so the numbers cannot substitute for futures returns. The project uses monthly changes because source frequency is monthly.

## Commercial commentary rules

- If latest 6-month annualised volatility >= 30%, flag elevated historical volatility.
- For buyer exposure: if latest 3-month cumulative price change >= +10%, flag increasing costs; if <= −10%, review procurement opportunity; otherwise routine checks.
- If Brent premium differs from the sample median by more than $2/bbl, flag benchmark spread review.
- These thresholds are deliberately transparent **illustrations**, not calibrated risk limits, price predictions or trading signals.

## Known limits

No intramonth path, no futures price/forward curve, no executable spot spread, no benchmark futures basis, no actual corporate position data, no cash-flow dates, no transaction costs, no evidence of hedge effectiveness, no stress-test confidence level, no forecast/backtest, no real-time updates. The 2026 partial year cannot be compared to complete years without careful qualification.
