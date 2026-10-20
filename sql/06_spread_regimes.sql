-- Business question: How frequently was the Brent premium above $5/bbl?
SELECT SUBSTR(month, 1, 4) AS calendar_year,
       COUNT(*) AS months_observed,
       SUM(CASE WHEN spread_usd_bbl > 5 THEN 1 ELSE 0 END) AS months_above_5_usd,
       ROUND(AVG(spread_usd_bbl), 2) AS avg_spread_usd_bbl
FROM monthly_market
GROUP BY SUBSTR(month, 1, 4)
ORDER BY calendar_year;
