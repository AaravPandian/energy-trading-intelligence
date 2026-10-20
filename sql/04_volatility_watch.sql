-- Business question: Which benchmark/month saw the highest six-month
-- rolling annualised volatility? (volatility estimated in Pandas.)
SELECT SUBSTR(month, 1, 7) AS month, benchmark,
       ROUND(100.0 * annualised_volatility, 2) AS vol_annualised_pct
FROM risk_metrics
WHERE annualised_volatility IS NOT NULL
ORDER BY annualised_volatility DESC
LIMIT 12;
