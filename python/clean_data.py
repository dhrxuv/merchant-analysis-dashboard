from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DATABASE_PATH = ROOT / "database" / "merchant_analytics.db"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"


SOURCE_FILES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "translations": "product_category_name_translation.csv",
}


def ensure_directories() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


def require_raw_files() -> None:
    missing = [name for name in SOURCE_FILES.values() if not (RAW_DIR / name).exists()]
    if missing:
        missing_text = "\n".join(f"- {name}" for name in missing)
        raise FileNotFoundError(
            "Missing raw dataset files in data/raw/.\n"
            f"Expected:\n{missing_text}\n"
            "See data/README.md for download instructions."
        )


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / SOURCE_FILES[name])


def normalize_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    for column in df.select_dtypes(include=["object", "string"]).columns:
        df[column] = df[column].astype("string").str.strip()
    return df


def prep_customers() -> pd.DataFrame:
    customers = normalize_text_columns(read_csv("customers"))
    customers = customers.drop_duplicates(subset=["customer_id"])
    customers["customer_city"] = customers["customer_city"].str.title()
    customers["customer_state"] = customers["customer_state"].str.upper()
    return customers


def prep_sellers() -> pd.DataFrame:
    sellers = normalize_text_columns(read_csv("sellers"))
    sellers = sellers.drop_duplicates(subset=["seller_id"])
    sellers["seller_city"] = sellers["seller_city"].str.title()
    sellers["seller_state"] = sellers["seller_state"].str.upper()
    return sellers


def prep_products() -> pd.DataFrame:
    products = normalize_text_columns(read_csv("products"))
    translations = normalize_text_columns(read_csv("translations"))
    products = products.merge(translations, on="product_category_name", how="left")
    return products.drop_duplicates(subset=["product_id"])


def prep_orders() -> pd.DataFrame:
    orders = normalize_text_columns(read_csv("orders"))
    datetime_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for column in datetime_cols:
        orders[column] = pd.to_datetime(orders[column], errors="coerce")

    orders["purchase_year"] = orders["order_purchase_timestamp"].dt.year
    orders["purchase_month"] = orders["order_purchase_timestamp"].dt.to_period("M").astype("string")
    orders["purchase_weekday"] = orders["order_purchase_timestamp"].dt.day_name()
    orders["is_weekend"] = orders["order_purchase_timestamp"].dt.dayofweek.isin([5, 6]).astype("int64")
    orders["delivery_days"] = (
        orders["order_delivered_customer_date"] - orders["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    orders["delivery_delay_days"] = (
        orders["order_delivered_customer_date"] - orders["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400
    orders["is_late_delivery"] = (orders["delivery_delay_days"] > 0).fillna(False).astype("int64")
    return orders.drop_duplicates(subset=["order_id"])


def prep_order_items() -> pd.DataFrame:
    order_items = normalize_text_columns(read_csv("order_items"))
    order_items["shipping_limit_date"] = pd.to_datetime(order_items["shipping_limit_date"], errors="coerce")
    return order_items.drop_duplicates(subset=["order_id", "order_item_id"])


def prep_payments() -> pd.DataFrame:
    payments = normalize_text_columns(read_csv("payments"))
    payments["payment_type"] = payments["payment_type"].fillna("unknown").str.lower()
    return payments.drop_duplicates(subset=["order_id", "payment_sequential"])


def prep_reviews() -> pd.DataFrame:
    reviews = normalize_text_columns(read_csv("reviews"))
    reviews["review_creation_date"] = pd.to_datetime(reviews["review_creation_date"], errors="coerce")
    reviews["review_answer_timestamp"] = pd.to_datetime(reviews["review_answer_timestamp"], errors="coerce")
    reviews = reviews.sort_values(["order_id", "review_answer_timestamp"])
    return reviews.drop_duplicates(subset=["order_id"], keep="last")


def prep_geolocation() -> pd.DataFrame:
    geolocation = normalize_text_columns(read_csv("geolocation"))
    geolocation["geolocation_city"] = geolocation["geolocation_city"].str.title()
    geolocation["geolocation_state"] = geolocation["geolocation_state"].str.upper()
    return geolocation


def export_processed_frames(frames: dict[str, pd.DataFrame]) -> None:
    for name, frame in frames.items():
        frame.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)


def build_database(frames: dict[str, pd.DataFrame]) -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        for table_name, frame in frames.items():
            frame.to_sql(table_name, connection, if_exists="append", index=False)


def main() -> None:
    ensure_directories()
    require_raw_files()

    frames = {
        "customers": prep_customers(),
        "sellers": prep_sellers(),
        "products": prep_products(),
        "orders": prep_orders(),
        "order_items": prep_order_items(),
        "payments": prep_payments(),
        "reviews": prep_reviews(),
        "geolocation": prep_geolocation(),
        "category_translation": normalize_text_columns(read_csv("translations")),
    }

    export_processed_frames(frames)
    build_database(frames)

    print(f"Processed data saved to: {PROCESSED_DIR}")
    print(f"SQLite database created at: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
