-- =========================================================================
-- 05  Products, geography and operations
-- =========================================================================

-- Q9. Category performance: revenue, margin, return rate
WITH line AS (
    SELECT p.category, o.status, oi.net_revenue, oi.cogs, oi.order_id
    FROM order_items oi
    JOIN orders o   USING (order_id)
    JOIN products p USING (product_id)
)
SELECT  category,
        ROUND(SUM(CASE WHEN status = 'delivered' THEN net_revenue END) / 1e6, 1) AS revenue_mln_kzt,
        ROUND(100.0 * SUM(CASE WHEN status = 'delivered' THEN net_revenue - cogs END)
                    / SUM(CASE WHEN status = 'delivered' THEN net_revenue END), 1) AS gross_margin_pct,
        ROUND(100.0 * COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END)
                    / COUNT(DISTINCT order_id), 1)                                AS return_rate_pct
FROM line
GROUP BY category
ORDER BY revenue_mln_kzt DESC;

-- Q10. Top 10 products by gross profit
SELECT  p.product_name, p.category,
        SUM(s.quantity)                              AS units,
        ROUND(SUM(s.net_revenue) / 1e6, 1)           AS revenue_mln_kzt,
        ROUND(SUM(s.net_revenue - s.cogs) / 1e6, 1)  AS gross_profit_mln_kzt
FROM v_sales s JOIN products p USING (product_id)
GROUP BY p.product_id
ORDER BY gross_profit_mln_kzt DESC
LIMIT 10;

-- Q11. Revenue by city with share of total and delivery speed
SELECT  c.city,
        COUNT(DISTINCT o.order_id)                                AS orders,
        ROUND(SUM(t.v) / 1e6, 1)                                  AS revenue_mln_kzt,
        ROUND(100.0 * SUM(t.v) / SUM(SUM(t.v)) OVER (), 1)        AS revenue_share_pct,
        ROUND(AVG(o.delivery_days), 1)                            AS avg_delivery_days,
        ROUND(AVG(o.review_score), 2)                             AS avg_review
FROM orders o
JOIN customers c USING (customer_id)
JOIN (SELECT order_id, SUM(net_revenue) v FROM order_items GROUP BY order_id) t USING (order_id)
WHERE o.status = 'delivered'
GROUP BY c.city
ORDER BY revenue_mln_kzt DESC;

-- Q12. Delivery speed vs customer satisfaction and returns
SELECT  CASE WHEN delivery_days <= 2 THEN '1-2 days'
             WHEN delivery_days <= 4 THEN '3-4 days'
             ELSE '5+ days' END                           AS delivery_bucket,
        COUNT(*)                                          AS orders,
        ROUND(AVG(review_score), 2)                       AS avg_review,
        ROUND(100.0 * AVG(review_score <= 2), 1)          AS low_review_pct,
        ROUND(100.0 * AVG(status = 'returned'), 1)        AS return_rate_pct
FROM orders
WHERE status <> 'cancelled'
GROUP BY delivery_bucket
ORDER BY delivery_bucket;

-- Q13. Discount effectiveness: promo vs full-price orders
SELECT  COALESCE(promo_code, '(none)')            AS promo_code,
        COUNT(DISTINCT order_id)                  AS orders,
        ROUND(SUM(net_revenue) / COUNT(DISTINCT order_id)) AS aov_kzt,
        ROUND(SUM(discount_amount) / 1e6, 1)      AS discount_given_mln_kzt,
        ROUND(100.0 * SUM(net_revenue - cogs) / SUM(net_revenue), 1) AS gross_margin_pct
FROM v_sales
GROUP BY promo_code
ORDER BY orders DESC;
