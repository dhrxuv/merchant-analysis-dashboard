# Dataset Instructions

This project is designed for the **Brazilian E-Commerce Public Dataset by Olist**.

Download the dataset from Kaggle and place these source files inside `data/raw/`:

- `olist_customers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `product_category_name_translation.csv`

Why this dataset:

- real-world merchant, order, payment, review, and delivery data
- strong fit for merchant analytics and business intelligence use cases
- supports SQL, Excel, Python, and Power BI storytelling

After adding the CSVs, run:

```powershell
& "C:\Users\dhruv\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" python\clean_data.py
& "C:\Users\dhruv\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" python\analysis.py
```
