"""
Clean the raw CSVs, write tidy files to data/processed/ and load everything
into a SQLite database (data/processed/dala_market.db) for the SQL analysis.

Usage:  python scripts/clean_data.py
"""
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

CITY_FIX = {
    "nur-sultan": "Astana", "astana": "Astana", "almaty": "Almaty",
    "shimkent": "Shymkent", "oskemen": "Ust-Kamenogorsk",
    "ust kamenogorsk": "Ust-Kamenogorsk", "karagandy": "Karaganda",
}


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    log = {"rows_in": len(df)}
    df = df.drop_duplicates()
    log["duplicates_removed"] = log["rows_in"] - len(df)
    city = df["city"].str.strip()
    df["city"] = city.str.lower().map(CITY_FIX).fillna(city.str.title().where(city.notna()))
    log["missing_city_to_unknown"] = int(df["city"].isna().sum())
    df["city"] = df["city"].fillna("Unknown")
    bad_age = ~df["birth_year"].between(1940, 2010)
    log["invalid_birth_year_nulled"] = int(bad_age.sum())
    df.loc[bad_age, "birth_year"] = np.nan
    df["birth_year"] = df["birth_year"].astype("Int64")
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    print("customers:", log)
    return df


def clean_items(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    df = df.drop_duplicates()
    print(f"order_items: removed {n - len(df)} duplicate rows")
    df["gross_revenue"] = df["quantity"] * df["unit_price"]
    df["discount_amount"] = (df["gross_revenue"] * df["discount_pct"]).round(0)
    df["net_revenue"] = df["gross_revenue"] - df["discount_amount"]
    return df


def main():
    customers = clean_customers(pd.read_csv(RAW / "customers.csv"))
    products = pd.read_csv(RAW / "products.csv")
    orders = pd.read_csv(RAW / "orders.csv", parse_dates=["order_date"])
    orders["delivery_days"] = orders["delivery_days"].astype("Int64")
    orders["review_score"] = orders["review_score"].astype("Int64")
    items = clean_items(pd.read_csv(RAW / "order_items.csv"))

    # referential-integrity checks
    assert orders["customer_id"].isin(customers["customer_id"]).all()
    assert items["order_id"].isin(orders["order_id"]).all()
    assert items["product_id"].isin(products["product_id"]).all()
    assert customers["customer_id"].is_unique and orders["order_id"].is_unique

    # cost of goods at line level
    items = items.merge(products[["product_id", "unit_cost"]], on="product_id")
    items["cogs"] = items["quantity"] * items["unit_cost"]
    items = items.drop(columns="unit_cost").sort_values("order_item_id")

    for name, df in [("customers", customers), ("products", products),
                     ("orders", orders), ("order_items", items)]:
        df.to_csv(OUT / f"{name}.csv", index=False, date_format="%Y-%m-%d")

    db = OUT / "dala_market.db"
    db.unlink(missing_ok=True)
    con = sqlite3.connect(db)
    con.executescript((ROOT / "sql" / "01_schema.sql").read_text())
    for name, df in [("customers", customers), ("products", products),
                     ("orders", orders), ("order_items", items)]:
        d = df.copy()
        for col in d.select_dtypes("datetime"):
            d[col] = d[col].dt.strftime("%Y-%m-%d")
        d.to_sql(name, con, if_exists="append", index=False)
    con.commit()
    con.close()
    print(f"SQLite database written to {db.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
