-- Business question: Which months had the largest Brent premium over WTI?
SELECT SUBSTR(month, 1, 7) AS month,
       brent_usd_bbl, wti_usd_bbl, spread_usd_bbl
FROM monthly_market
ORDER BY spread_usd_bbl DESC
LIMIT 12;
