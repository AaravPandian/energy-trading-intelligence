-- Business question: Which months had the largest absolute price moves?
WITH movements AS (
    SELECT month, benchmark, price_usd_bbl,
           ROUND(100.0 * (price_usd_bbl / LAG(price_usd_bbl) OVER (
               PARTITION BY benchmark ORDER BY month) - 1), 2) AS return_pct
    FROM spot_prices
)
SELECT SUBSTR(month, 1, 7) AS month, benchmark,
       price_usd_bbl, return_pct
FROM movements
WHERE return_pct IS NOT NULL
ORDER BY ABS(return_pct) DESC
LIMIT 15;
