-- Business question: What does the last published month tell us?
SELECT SUBSTR(s.month, 1, 7) AS month, s.benchmark,
       s.price_usd_bbl AS price_usd_bbl,
       ROUND(r.monthly_return * 100, 2) AS monthly_return_pct,
       ROUND(r.annualised_volatility * 100, 2) AS six_month_ann_vol_pct
FROM spot_prices s
JOIN risk_metrics r
  ON s.month = r.month AND s.benchmark = r.benchmark
WHERE s.month = (SELECT MAX(month) FROM spot_prices)
ORDER BY s.benchmark;
