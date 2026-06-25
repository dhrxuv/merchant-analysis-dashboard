-- Merchant Analytics Dashboard
-- 20 recruiter-friendly business intelligence queries for the Olist analytical model.

-- 1. Total revenue
SELECT ROUND(SUM(payment_value), 2) AS total_revenue
FROM payments;

-- 2. Total completed orders
SELECT COUNT(*) AS delivered_orders
FROM orders
WHERE order_status = 'delivered';

-- 3. Monthly revenue trend
SELECT
    o.purchase_month,
    ROUND(SUM(p.payment_value), 2) AS monthly_revenue
FROM orders o
JOIN payments p ON o.order_id = p.order_id
GROUP BY o.purchase_month
ORDER BY o.purchase_month;

-- 4. Monthly order trend
SELECT
    purchase_month,
    COUNT(*) AS orders_count
FROM orders
GROUP BY purchase_month
ORDER BY purchase_month;

-- 5. Average order value
SELECT ROUND(SUM(payment_value) / COUNT(DISTINCT order_id), 2) AS average_order_value
FROM payments;

-- 6. Top 10 merchants by revenue
SELECT
    oi.seller_id,
    s.seller_state,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS seller_revenue
FROM order_items oi
JOIN sellers s ON oi.seller_id = s.seller_id
GROUP BY oi.seller_id, s.seller_state
ORDER BY seller_revenue DESC
LIMIT 10;

-- 7. Revenue concentration among top 5% merchants
WITH seller_revenue AS (
    SELECT
        seller_id,
        SUM(price + freight_value) AS revenue
    FROM order_items
    GROUP BY seller_id
),
ranked AS (
    SELECT
        seller_id,
        revenue,
        NTILE(20) OVER (ORDER BY revenue DESC) AS revenue_bucket
    FROM seller_revenue
)
SELECT
    ROUND(
        100.0 * SUM(CASE WHEN revenue_bucket = 1 THEN revenue ELSE 0 END) / SUM(revenue),
        2
    ) AS top_5_percent_revenue_share
FROM ranked;

-- 8. Cancellation rate
SELECT
    ROUND(100.0 * SUM(CASE WHEN order_status IN ('canceled', 'unavailable') THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS cancellation_rate_pct
FROM orders;

-- 9. Revenue lost due to cancellations
SELECT
    ROUND(SUM(p.payment_value), 2) AS canceled_order_value
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_status IN ('canceled', 'unavailable');

-- 10. Payment method distribution
SELECT
    payment_type,
    COUNT(*) AS payments_count,
    ROUND(SUM(payment_value), 2) AS payment_revenue
FROM payments
GROUP BY payment_type
ORDER BY payment_revenue DESC;

-- 11. Weekend vs weekday revenue
SELECT
    CASE WHEN is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    ROUND(SUM(p.payment_value), 2) AS revenue
FROM orders o
JOIN payments p ON o.order_id = p.order_id
GROUP BY day_type
ORDER BY revenue DESC;

-- 12. Revenue by customer state
SELECT
    c.customer_state,
    ROUND(SUM(p.payment_value), 2) AS revenue
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN payments p ON o.order_id = p.order_id
GROUP BY c.customer_state
ORDER BY revenue DESC;

-- 13. Top 10 cities by orders
SELECT
    c.customer_city,
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS orders_count
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_city, c.customer_state
ORDER BY orders_count DESC
LIMIT 10;

-- 14. Average basket size
SELECT ROUND(AVG(item_count), 2) AS average_basket_size
FROM (
    SELECT order_id, COUNT(*) AS item_count
    FROM order_items
    GROUP BY order_id
);

-- 15. Most popular product categories
SELECT
    COALESCE(product_category_name_english, product_category_name, 'unknown') AS category,
    COUNT(*) AS items_sold,
    ROUND(SUM(price), 2) AS category_revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY category
ORDER BY category_revenue DESC
LIMIT 10;

-- 16. Average review score by merchant
SELECT
    oi.seller_id,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    COUNT(DISTINCT oi.order_id) AS rated_orders
FROM order_items oi
JOIN reviews r ON oi.order_id = r.order_id
GROUP BY oi.seller_id
HAVING rated_orders >= 20
ORDER BY avg_review_score DESC, rated_orders DESC
LIMIT 10;

-- 17. Late delivery rate
SELECT
    ROUND(100.0 * SUM(CASE WHEN is_late_delivery = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_delivery_rate_pct
FROM orders
WHERE order_status = 'delivered';

-- 18. Average delivery delay by merchant state
SELECT
    s.seller_state,
    ROUND(AVG(o.delivery_delay_days), 2) AS avg_delay_days
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN sellers s ON oi.seller_id = s.seller_id
WHERE o.order_status = 'delivered'
  AND o.delivery_delay_days IS NOT NULL
GROUP BY s.seller_state
ORDER BY avg_delay_days DESC;

-- 19. Customer lifetime value and repeat behavior
WITH customer_summary AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS orders_count,
        SUM(p.payment_value) AS customer_revenue
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN payments p ON o.order_id = p.order_id
    GROUP BY c.customer_unique_id
)
SELECT
    ROUND(AVG(customer_revenue), 2) AS avg_customer_ltv,
    ROUND(AVG(CASE WHEN orders_count > 1 THEN customer_revenue END), 2) AS repeat_customer_ltv,
    ROUND(
        AVG(CASE WHEN orders_count > 1 THEN customer_revenue END) /
        NULLIF(AVG(CASE WHEN orders_count = 1 THEN customer_revenue END), 0),
        2
    ) AS repeat_vs_single_ltv_multiple
FROM customer_summary;

-- 20. Cohort retention by first purchase month
WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        substr(o.order_purchase_timestamp, 1, 7) AS order_month,
        MIN(substr(o.order_purchase_timestamp, 1, 7)) OVER (
            PARTITION BY c.customer_unique_id
        ) AS cohort_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
),
cohorts AS (
    SELECT DISTINCT
        customer_unique_id,
        cohort_month,
        order_month
    FROM customer_orders
)
SELECT
    cohort_month,
    order_month,
    COUNT(DISTINCT customer_unique_id) AS retained_customers
FROM cohorts
GROUP BY cohort_month, order_month
ORDER BY cohort_month, order_month;

-- 21. Merchant health score and risk tiering
WITH merchant_metrics AS (
    SELECT
        oi.seller_id,
        ROUND(SUM(oi.price + oi.freight_value), 2) AS revenue,
        COUNT(DISTINCT oi.order_id) AS orders_count,
        ROUND(AVG(r.review_score), 2) AS avg_review_score,
        ROUND(100.0 * AVG(CASE WHEN o.is_late_delivery = 1 THEN 1 ELSE 0 END), 2) AS late_delivery_rate_pct,
        ROUND(100.0 * AVG(CASE WHEN o.order_status IN ('canceled', 'unavailable') THEN 1 ELSE 0 END), 2)
            AS cancellation_rate_pct
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN reviews r ON oi.order_id = r.order_id
    GROUP BY oi.seller_id
),
scored AS (
    SELECT
        seller_id,
        revenue,
        orders_count,
        avg_review_score,
        late_delivery_rate_pct,
        cancellation_rate_pct,
        ROUND(
            (
                0.40 * PERCENT_RANK() OVER (ORDER BY revenue) +
                0.25 * COALESCE(avg_review_score / 5.0, 0) +
                0.20 * (1 - COALESCE(late_delivery_rate_pct, 100) / 100.0) +
                0.15 * (1 - COALESCE(cancellation_rate_pct, 100) / 100.0)
            ) * 100,
            2
        ) AS merchant_health_score
    FROM merchant_metrics
)
SELECT
    seller_id,
    revenue,
    orders_count,
    avg_review_score,
    late_delivery_rate_pct,
    cancellation_rate_pct,
    merchant_health_score,
    CASE
        WHEN revenue >= (
            SELECT percentile_revenue
            FROM (
                SELECT revenue AS percentile_revenue
                FROM scored
                ORDER BY revenue DESC
                LIMIT 1 OFFSET CAST((SELECT COUNT(*) * 0.2 FROM scored) AS INTEGER)
            )
        )
        AND merchant_health_score >= 70 THEN 'High Value / Healthy'
        WHEN revenue >= (
            SELECT percentile_revenue
            FROM (
                SELECT revenue AS percentile_revenue
                FROM scored
                ORDER BY revenue DESC
                LIMIT 1 OFFSET CAST((SELECT COUNT(*) * 0.2 FROM scored) AS INTEGER)
            )
        )
        AND merchant_health_score < 70 THEN 'High Value / At Risk'
        WHEN merchant_health_score >= 70 THEN 'Low Value / Healthy'
        ELSE 'Low Value / At Risk'
    END AS merchant_segment
FROM scored
ORDER BY merchant_health_score DESC, revenue DESC;

-- 22. Merchants needing intervention
WITH merchant_health AS (
    SELECT
        oi.seller_id,
        ROUND(SUM(oi.price + oi.freight_value), 2) AS revenue,
        ROUND(AVG(r.review_score), 2) AS avg_review_score,
        ROUND(100.0 * AVG(CASE WHEN o.is_late_delivery = 1 THEN 1 ELSE 0 END), 2) AS late_delivery_rate_pct,
        ROUND(100.0 * AVG(CASE WHEN o.order_status IN ('canceled', 'unavailable') THEN 1 ELSE 0 END), 2)
            AS cancellation_rate_pct
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN reviews r ON oi.order_id = r.order_id
    GROUP BY oi.seller_id
)
SELECT
    seller_id,
    revenue,
    avg_review_score,
    late_delivery_rate_pct,
    cancellation_rate_pct
FROM merchant_health
WHERE revenue > (
    SELECT AVG(revenue) FROM merchant_health
)
  AND (
      avg_review_score < 3.8
      OR late_delivery_rate_pct > 12
      OR cancellation_rate_pct > 2
  )
ORDER BY revenue DESC, late_delivery_rate_pct DESC;
