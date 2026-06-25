# Merchant Analytics Dashboard: SQL, Excel & Python Business Intelligence

An end-to-end analytics project using SQL, Python, Excel, and Power BI concepts to analyze marketplace transaction data, generate business KPIs, and uncover revenue, retention, and operational insights.

## Why This Project

This project is built as a business-facing analytics case study on the **Brazilian E-Commerce Public Dataset by Olist**, which includes customers, merchants, products, payments, reviews, and delivery timelines.

That makes it a strong fit for answering questions like:

- Which merchants drive the most revenue?
- What does monthly order and revenue growth look like?
- How concentrated is revenue across top sellers?
- Which payment methods dominate merchant sales?
- How strong is customer retention?
- Where are operational issues like delays and cancellations hurting the business?

## Tech Stack

- Python
- SQL (SQLite-ready, PostgreSQL-portable logic)
- Pandas
- Excel
- Power BI
- Git

## Dataset

Source dataset: **Brazilian E-Commerce Public Dataset by Olist**

Tables used:

- customers
- sellers
- products
- orders
- order items
- payments
- reviews
- geolocation
- product category translation

Place the raw CSV files in [data/raw](C:/Users/dhruv/Documents/merchant%20analysis%20dashboard/data/raw) using the instructions in [data/README.md](C:/Users/dhruv/Documents/merchant%20analysis%20dashboard/data/README.md).

## Folder Structure

```text
merchant-analytics-dashboard/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── exports/
│   └── README.md
├── database/
├── excel/
├── powerbi/
├── python/
├── sql/
├── .gitignore
├── README.md
└── requirements.txt
```

## End-to-End Workflow

1. Download the Olist dataset and copy the CSV files into `data/raw/`.
2. Run [python/clean_data.py](C:/Users/dhruv/Documents/merchant%20analysis%20dashboard/python/clean_data.py) to clean raw data, engineer delivery and date features, and build a SQLite database.
3. Run [python/analysis.py](C:/Users/dhruv/Documents/merchant%20analysis%20dashboard/python/analysis.py) to generate KPI and chart-ready exports.
4. Build the Excel dashboard manually from the cleaned exports in `data/exports/`.
5. Optionally build a Power BI dashboard using the same exports.

Bundled runtime command:

```powershell
& "C:\Users\dhruv\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" python\clean_data.py
& "C:\Users\dhruv\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" python\analysis.py
```

## SQL Analysis

The SQL layer is intentionally business-oriented rather than purely technical. See:

- [sql/schema.sql](C:/Users/dhruv/Documents/merchant%20analysis%20dashboard/sql/schema.sql)
- [sql/analysis.sql](C:/Users/dhruv/Documents/merchant%20analysis%20dashboard/sql/analysis.sql)

Business questions covered:

- Total revenue
- Delivered orders
- Monthly revenue trend
- Monthly order trend
- Average order value
- Top 10 merchants by revenue
- Revenue concentration among top 5% merchants
- Cancellation rate
- Revenue lost due to cancellations
- Payment method distribution
- Weekend vs weekday revenue
- Revenue by customer state
- Top cities by orders
- Average basket size
- Most popular product categories
- Average review score by merchant
- Late delivery rate
- Average delivery delay by merchant state
- Customer lifetime value
- Cohort retention
- Merchant health score and segmentation
- High-value merchants needing intervention

## Python Analysis

[python/clean_data.py](C:/Users/dhruv/Documents/merchant%20analysis%20dashboard/python/clean_data.py) handles:

- missing-value-safe parsing
- duplicate removal
- datetime conversion
- feature engineering for month, weekday, weekend, delivery days, and delay days
- translation joins for category names
- export of cleaned tables
- creation of a SQLite analytical database

[python/analysis.py](C:/Users/dhruv/Documents/merchant%20analysis%20dashboard/python/analysis.py) exports:

- KPI summary
- monthly revenue
- payment mix
- top merchants
- revenue by state
- delivery summary
- review distribution
- category performance
- merchant health score
- intervention candidates
- cohort retention

## Excel Dashboard

The Excel dashboard is intended to be built manually from the exports in `data/exports/`.

Recommended Excel tabs:

- Dashboard
- Monthly Revenue
- Top Merchants
- Revenue by State
- Payment Mix
- Merchant Health
- At Risk Merchants
- Retention

Recommended Excel features:

- Pivot Tables
- Pivot Charts
- Slicers
- Timeline filters
- Conditional formatting
- KPI cards
- Segment summaries

## Merchant Health Score

To make the project more decision-oriented, the analysis now includes a **Merchant Health Score** for each seller.

The score blends:

- revenue contribution
- review quality
- late delivery rate
- cancellation rate

This creates four business-friendly merchant segments:

- High Value / Healthy
- High Value / At Risk
- Low Value / Healthy
- Low Value / At Risk

This is useful because it turns raw reporting into account prioritization instead of stopping at descriptive dashboards.

## Power BI

Use the exports in `data/exports/` to create:

- Executive Summary
- Merchant Performance
- Customer Retention
- Delivery Operations
- Customer Experience

See [powerbi/README.md](C:/Users/dhruv/Documents/merchant%20analysis%20dashboard/powerbi/README.md).

## Current Dataset-Backed Highlights

Based on the loaded Olist dataset in this repo:

- total revenue is `R$ 16.01M` across `99,441` orders
- average order value is `R$ 160.99`
- repeat customer rate is `3.12%`
- late delivery rate is `8.11%`
- average review score is `4.09`

Business interpretation:

- payment mix and monthly revenue trends can be used to discuss monetization and checkout behavior
- low repeat rate suggests retention upside, especially through CRM or loyalty plays
- late-delivery pockets can be tied to merchant operations and customer experience
- Merchant Health Score highlights which high-value sellers deserve proactive support

## Recommendations

- Prioritize account management for `High Value / At Risk` merchants before operational issues hurt revenue.
- Use retention campaigns and CRM nudges to improve the relatively low repeat customer rate.
- Track late-delivery-heavy merchants or regions with an exception dashboard and weekly escalation list.
- Combine reviews, cancellations, and delays into a merchant success workflow rather than viewing each metric in isolation.

## Deliverables

- cleaned CSVs in `data/processed/`
- SQLite database in `database/merchant_analytics.db`
- chart-ready exports in `data/exports/`

## Notes

The repository focuses on the analytical pipeline and source files. Local outputs such as databases, dashboard screenshots, and workbook versions can be created from the processed data and exports as needed.
