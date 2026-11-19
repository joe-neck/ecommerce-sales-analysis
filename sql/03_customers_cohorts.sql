-- =========================================================================
-- 03  Customers: repeat rate, cohort retention, channel quality
-- =========================================================================

-- Q5. Repeat-purchase rate (share of customers with 2+ delivered orders)
WITH per_customer AS (
    SELECT customer_id, COUNT(DISTINCT order_id) AS n_orders
    FROM v_sales GROUP BY customer_id
)
SELECT  COUNT(*)                                                   AS buyers,
        SUM(n_orders >= 2)                                         AS repeat_buyers,
        ROUND(100.0 * SUM(n_orders >= 2) / COUNT(*), 1)            AS repeat_rate_pct,
        ROUND(AVG(n_orders), 2)                                    AS avg_orders_per_buyer
FROM per_customer;

-- Q6. Quarterly cohort retention
--     (% of each first-purchase cohort that bought again N quarters later)
WITH first_order AS (
    SELECT customer_id, MIN(order_date) AS first_date
    FROM v_sales GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT s.customer_id,
           strftime('%Y', f.first_date) || '-Q' || ((CAST(strftime('%m', f.first_date) AS INT) + 2) / 3) AS cohort,
           (CAST(strftime('%Y', s.order_date) AS INT) - CAST(strftime('%Y', f.first_date) AS INT)) * 4
           + ((CAST(strftime('%m', s.order_date) AS INT) + 2) / 3)
           - ((CAST(strftime('%m', f.first_date) AS INT) + 2) / 3)  AS quarter_n
    FROM v_sales s JOIN first_order f USING (customer_id)
),
sizes AS (SELECT cohort, COUNT(DISTINCT customer_id) AS cohort_size FROM activity WHERE quarter_n = 0 GROUP BY cohort)
SELECT  a.cohort, s.cohort_size, a.quarter_n,
        ROUND(100.0 * COUNT(DISTINCT a.customer_id) / s.cohort_size, 1) AS retention_pct
FROM activity a JOIN sizes s USING (cohort)
GROUP BY a.cohort, a.quarter_n
ORDER BY a.cohort, a.quarter_n;

-- Q7. Acquisition-channel quality: value per customer and return rate
WITH cust AS (
    SELECT c.customer_id, c.acquisition_channel,
           COUNT(DISTINCT CASE WHEN o.status = 'delivered' THEN o.order_id END) AS delivered_orders,
           SUM(o.status = 'returned')                                           AS returned_orders,
           COUNT(o.order_id)                                                    AS all_orders
    FROM customers c LEFT JOIN orders o USING (customer_id)
    GROUP BY c.customer_id
),
rev AS (SELECT customer_id, SUM(net_revenue) AS revenue, SUM(net_revenue - cogs) AS profit
        FROM v_sales GROUP BY customer_id)
SELECT  acquisition_channel,
        COUNT(*)                                           AS customers,
        ROUND(AVG(all_orders), 2)                          AS orders_per_customer,
        ROUND(100.0 * SUM(returned_orders) / SUM(all_orders), 1) AS return_rate_pct,
        ROUND(AVG(COALESCE(revenue, 0)))                   AS revenue_per_customer_kzt,
        ROUND(AVG(COALESCE(profit, 0)))                    AS profit_per_customer_kzt
FROM cust LEFT JOIN rev USING (customer_id)
GROUP BY acquisition_channel
ORDER BY profit_per_customer_kzt DESC;
