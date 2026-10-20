-- Business question: How did average Brent/WTI prices change by year?
-- Important: 2026 is only Jan-Aug, so it is a year-to-date mean.
SELECT SUBSTR(month, 1, 4) AS calendar_year,
       COUNT(*) AS months_in_sample,
       ROUND(AVG(brent_usd_bbl), 2) AS avg_brent_usd_bbl,
       ROUND(AVG(wti_usd_bbl), 2) AS avg_wti_usd_bbl,
       ROUND(AVG(spread_usd_bbl), 2) AS avg_spread_usd_bbl
FROM monthly_market
GROUP BY SUBSTR(month, 1, 4)
ORDER BY calendar_year;
