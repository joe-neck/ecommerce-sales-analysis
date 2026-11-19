-- =========================================================================
-- 02  Headline KPIs and revenue trend
-- Revenue = net revenue (after discounts) of DELIVERED orders, in KZT
-- =========================================================================

-- Q1. Headline KPIs by year
SELECT  strftime('%Y', order_date)                         AS year,
        COUNT(DISTINCT order_id)                           AS orders,
        COUNT(DISTINCT customer_id)                        AS active_customers,
        ROUND(SUM(net_revenue) / 1e6, 1)                   AS revenue_mln_kzt,
        ROUND(SUM(net_revenue - cogs) / 1e6, 1)            AS gross_profit_mln_kzt,
        ROUND(100.0 * SUM(net_revenue - cogs) / SUM(net_revenue), 1) AS gross_margin_pct,
        ROUND(SUM(net_revenue) / COUNT(DISTINCT order_id)) AS aov_kzt
FROM v_sales
GROUP BY year
ORDER BY year;

-- Q2. Monthly revenue with month-over-month and year-over-year growth
WITH monthly AS (
    SELECT strftime('%Y-%m', order_date) AS month,
           SUM(net_revenue)              AS revenue
    FROM v_sales
    GROUP BY month
)
SELECT  month,
        ROUND(revenue / 1e6, 1) AS revenue_mln_kzt,
        ROUND(100.0 * (revenue - LAG(revenue, 1)  OVER (ORDER BY month))
                    / LAG(revenue, 1)  OVER (ORDER BY month), 1) AS mom_growth_pct,
        ROUND(100.0 * (revenue - LAG(revenue, 12) OVER (ORDER BY month))
                    / LAG(revenue, 12) OVER (ORDER BY month), 1) AS yoy_growth_pct
FROM monthly
ORDER BY month;

-- Q3. Order status mix (how much demand is lost to returns / cancellations)
SELECT  o.status,
        COUNT(*)                                            AS orders,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)  AS share_pct,
        ROUND(SUM(t.order_value) / 1e6, 1)                  AS value_mln_kzt
FROM orders o
JOIN (SELECT order_id, SUM(net_revenue) AS order_value
      FROM order_items GROUP BY order_id) t USING (order_id)
GROUP BY o.status
ORDER BY orders DESC;

-- Q4. Top 5 sales days (promo effect)
SELECT  order_date,
        COUNT(DISTINCT order_id)         AS orders,
        ROUND(SUM(net_revenue) / 1e6, 1) AS revenue_mln_kzt,
        GROUP_CONCAT(DISTINCT promo_code) AS promo_codes
FROM v_sales
GROUP BY order_date
ORDER BY SUM(net_revenue) DESC
LIMIT 5;
