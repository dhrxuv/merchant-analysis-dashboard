from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "database" / "merchant_analytics.db"
EXPORT_DIR = ROOT / "data" / "exports"


def require_database() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            "Database not found. Run python/clean_data.py after placing the Olist CSV files in data/raw/."
        )


def query(connection: sqlite3.Connection, sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, connection)


def export_frame(frame: pd.DataFrame, name: str) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(EXPORT_DIR / f"{name}.csv", index=False)


def main() -> None:
    require_database()

    with sqlite3.connect(DATABASE_PATH) as connection:
        kpi_summary = query(
            connection,
            """
            WITH customer_rollup AS (
                SELECT
                    c.customer_unique_id,
                    COUNT(DISTINCT o.order_id) AS orders_count,
                    SUM(p.payment_value) AS customer_revenue
                FROM customers c
                JOIN orders o ON c.customer_id = o.customer_id
                JOIN payments p ON o.order_id = p.order_id
                GROUP BY c.customer_unique_id
            ),
            top_merchant AS (
                SELECT
                    seller_id,
                    ROUND(SUM(price + freight_value), 2) AS merchant_revenue
                FROM order_items
                GROUP BY seller_id
                ORDER BY merchant_revenue DESC
                LIMIT 1
            )
            SELECT 'Total Revenue' AS metric, ROUND(SUM(payment_value), 2) AS value FROM payments
            UNION ALL
            SELECT 'Total Orders', COUNT(DISTINCT order_id) FROM orders
            UNION ALL
            SELECT 'Average Order Value', ROUND(SUM(payment_value) / COUNT(DISTINCT order_id), 2) FROM payments
            UNION ALL
            SELECT 'Unique Customers', COUNT(DISTINCT customer_unique_id) FROM customers
            UNION ALL
            SELECT 'Repeat Customer Rate %',
                ROUND(100.0 * AVG(CASE WHEN orders_count > 1 THEN 1 ELSE 0 END), 2)
            FROM customer_rollup
            UNION ALL
            SELECT 'Cancellation Rate %',
                ROUND(100.0 * SUM(CASE WHEN order_status IN ('canceled', 'unavailable') THEN 1 ELSE 0 END) / COUNT(*), 2)
            FROM orders
            UNION ALL
            SELECT 'Average Delivery Days',
                ROUND(AVG(delivery_days), 2)
            FROM orders
            WHERE order_status = 'delivered'
            UNION ALL
            SELECT 'Late Delivery Rate %',
                ROUND(100.0 * AVG(CASE WHEN is_late_delivery = 1 THEN 1 ELSE 0 END), 2)
            FROM orders
            WHERE order_status = 'delivered'
            UNION ALL
            SELECT 'Average Review Score', ROUND(AVG(review_score), 2) FROM reviews
            UNION ALL
            SELECT 'Top Merchant Revenue', merchant_revenue FROM top_merchant
            """,
        )

        monthly_revenue = query(
            connection,
            """
            SELECT
                o.purchase_month,
                ROUND(SUM(p.payment_value), 2) AS revenue,
                COUNT(DISTINCT o.order_id) AS orders,
                ROUND(SUM(p.payment_value) / COUNT(DISTINCT o.order_id), 2) AS aov
            FROM orders o
            JOIN payments p ON o.order_id = p.order_id
            GROUP BY o.purchase_month
            ORDER BY o.purchase_month
            """,
        )

        payment_mix = query(
            connection,
            """
            SELECT
                payment_type,
                COUNT(*) AS payments_count,
                ROUND(SUM(payment_value), 2) AS revenue
            FROM payments
            GROUP BY payment_type
            ORDER BY revenue DESC
            """,
        )

        top_merchants = query(
            connection,
            """
            SELECT
                oi.seller_id,
                s.seller_state,
                COUNT(DISTINCT oi.order_id) AS orders_count,
                ROUND(SUM(oi.price + oi.freight_value), 2) AS revenue,
                ROUND(AVG(r.review_score), 2) AS avg_review_score
            FROM order_items oi
            JOIN sellers s ON oi.seller_id = s.seller_id
            LEFT JOIN reviews r ON oi.order_id = r.order_id
            GROUP BY oi.seller_id, s.seller_state
            ORDER BY revenue DESC
            LIMIT 15
            """,
        )

        revenue_by_state = query(
            connection,
            """
            SELECT
                c.customer_state,
                ROUND(SUM(p.payment_value), 2) AS revenue,
                COUNT(DISTINCT o.order_id) AS orders_count
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN payments p ON o.order_id = p.order_id
            GROUP BY c.customer_state
            ORDER BY revenue DESC
            """,
        )

        delivery_summary = query(
            connection,
            """
            SELECT
                purchase_month,
                ROUND(AVG(delivery_days), 2) AS avg_delivery_days,
                ROUND(AVG(delivery_delay_days), 2) AS avg_delay_days,
                ROUND(100.0 * AVG(CASE WHEN is_late_delivery = 1 THEN 1 ELSE 0 END), 2) AS late_delivery_rate_pct
            FROM orders
            WHERE order_status = 'delivered'
            GROUP BY purchase_month
            ORDER BY purchase_month
            """,
        )

        review_distribution = query(
            connection,
            """
            SELECT
                review_score,
                COUNT(*) AS reviews_count
            FROM reviews
            GROUP BY review_score
            ORDER BY review_score
            """,
        )

        category_performance = query(
            connection,
            """
            SELECT
                COALESCE(product_category_name_english, product_category_name, 'unknown') AS category,
                COUNT(*) AS items_sold,
                ROUND(SUM(price), 2) AS revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            GROUP BY category
            ORDER BY revenue DESC
            LIMIT 15
            """,
        )

        merchant_health = query(
            connection,
            """
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
            ),
            thresholds AS (
                SELECT
                    AVG(revenue) AS avg_revenue,
                    AVG(merchant_health_score) AS avg_health
                FROM scored
            )
            SELECT
                s.seller_id,
                s.revenue,
                s.orders_count,
                s.avg_review_score,
                s.late_delivery_rate_pct,
                s.cancellation_rate_pct,
                s.merchant_health_score,
                CASE
                    WHEN s.revenue >= t.avg_revenue AND s.merchant_health_score >= t.avg_health THEN 'High Value / Healthy'
                    WHEN s.revenue >= t.avg_revenue AND s.merchant_health_score < t.avg_health THEN 'High Value / At Risk'
                    WHEN s.revenue < t.avg_revenue AND s.merchant_health_score >= t.avg_health THEN 'Low Value / Healthy'
                    ELSE 'Low Value / At Risk'
                END AS merchant_segment
            FROM scored s
            CROSS JOIN thresholds t
            ORDER BY s.merchant_health_score DESC, s.revenue DESC
            """,
        )

        intervention_candidates = query(
            connection,
            """
            WITH merchant_health AS (
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
            )
            SELECT
                seller_id,
                revenue,
                orders_count,
                avg_review_score,
                late_delivery_rate_pct,
                cancellation_rate_pct
            FROM merchant_health
            WHERE revenue > (SELECT AVG(revenue) FROM merchant_health)
              AND (
                  avg_review_score < 3.8
                  OR late_delivery_rate_pct > 12
                  OR cancellation_rate_pct > 2
              )
            ORDER BY revenue DESC, late_delivery_rate_pct DESC
            LIMIT 20
            """,
        )

        retention = query(
            connection,
            """
            WITH customer_months AS (
                SELECT
                    c.customer_unique_id,
                    MIN(o.purchase_month) AS cohort_month,
                    o.purchase_month AS activity_month
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                GROUP BY c.customer_unique_id, o.purchase_month
            ),
            cohort_sizes AS (
                SELECT cohort_month, COUNT(DISTINCT customer_unique_id) AS cohort_size
                FROM customer_months
                GROUP BY cohort_month
            )
            SELECT
                cm.cohort_month,
                cm.activity_month,
                COUNT(DISTINCT cm.customer_unique_id) AS active_customers,
                cs.cohort_size,
                ROUND(100.0 * COUNT(DISTINCT cm.customer_unique_id) / cs.cohort_size, 2) AS retention_rate_pct
            FROM customer_months cm
            JOIN cohort_sizes cs ON cm.cohort_month = cs.cohort_month
            GROUP BY cm.cohort_month, cm.activity_month, cs.cohort_size
            ORDER BY cm.cohort_month, cm.activity_month
            """,
        )

    frames = {
        "kpi_summary": kpi_summary,
        "monthly_revenue": monthly_revenue,
        "payment_mix": payment_mix,
        "top_merchants": top_merchants,
        "revenue_by_state": revenue_by_state,
        "delivery_summary": delivery_summary,
        "review_distribution": review_distribution,
        "category_performance": category_performance,
        "merchant_health": merchant_health,
        "intervention_candidates": intervention_candidates,
        "retention": retention,
    }

    for name, frame in frames.items():
        export_frame(frame, name)

    print(f"Analysis exports saved to: {EXPORT_DIR}")


if __name__ == "__main__":
    main()
