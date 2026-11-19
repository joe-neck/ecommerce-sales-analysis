-- =========================================================================
-- 04  RFM segmentation (Recency, Frequency, Monetary)
-- Snapshot date = day after the last order in the data (2026-01-01)
-- =========================================================================

WITH rfm_raw AS (
    SELECT  customer_id,
            JULIANDAY('2026-01-01') - JULIANDAY(MAX(order_date)) AS recency_days,
            COUNT(DISTINCT order_id)                            AS frequency,
            SUM(net_revenue)                                    AS monetary
    FROM v_sales
    GROUP BY customer_id
),
scored AS (
    SELECT  *,
            6 - NTILE(5) OVER (ORDER BY recency_days)  AS r,   -- recent = 5
            CASE WHEN frequency >= 5 THEN 5 WHEN frequency = 4 THEN 4
                 WHEN frequency = 3 THEN 3 WHEN frequency = 2 THEN 2 ELSE 1 END AS f,
            NTILE(5) OVER (ORDER BY monetary)          AS m
    FROM rfm_raw
),
segmented AS (
    SELECT *,
        CASE
            WHEN r >= 4 AND f >= 4                 THEN 'Champions'
            WHEN r >= 3 AND f >= 3                 THEN 'Loyal'
            WHEN r >= 4 AND f <= 2                 THEN 'New / Promising'
            WHEN r = 3  AND f <= 2                 THEN 'Need Attention'
            WHEN r <= 2 AND (f >= 3 OR m >= 4)     THEN 'At Risk (high value)'
            ELSE 'Hibernating'
        END AS segment
    FROM scored
)
-- Q8. Segment summary
SELECT  segment,
        COUNT(*)                                              AS customers,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)    AS customers_pct,
        ROUND(AVG(recency_days))                              AS avg_recency_days,
        ROUND(AVG(frequency), 2)                              AS avg_orders,
        ROUND(SUM(monetary) / 1e6, 1)                         AS revenue_mln_kzt,
        ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1) AS revenue_pct
FROM segmented
GROUP BY segment
ORDER BY revenue_mln_kzt DESC;
