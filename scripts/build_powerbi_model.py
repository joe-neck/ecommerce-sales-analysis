"""
Export a star-schema model for Power BI / Tableau to powerbi/model/:

  fact_sales.csv     one row per order line (grain: order_item_id)
  dim_date.csv       calendar 2024-01-01 .. 2025-12-31
  dim_customer.csv   customer attributes + RFM segment
  dim_product.csv    product attributes
  dim_order.csv      order-level attributes (status, payment, promo, delivery, review)

Usage:  python scripts/build_powerbi_model.py   (run the notebook first for RFM segments)
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "powerbi" / "model"
OUT.mkdir(parents=True, exist_ok=True)

customers = pd.read_csv(PROC / "customers.csv")
products = pd.read_csv(PROC / "products.csv")
orders = pd.read_csv(PROC / "orders.csv", parse_dates=["order_date"])
items = pd.read_csv(PROC / "order_items.csv")

# fact
fact = items.merge(orders[["order_id", "customer_id", "order_date"]], on="order_id")
fact["date_key"] = fact["order_date"].dt.strftime("%Y%m%d").astype(int)
fact = fact[["order_item_id", "order_id", "date_key", "customer_id", "product_id", "quantity",
             "unit_price", "discount_pct", "gross_revenue", "discount_amount", "net_revenue", "cogs"]]
fact.to_csv(OUT / "fact_sales.csv", index=False)

# date dimension
d = pd.DataFrame({"date": pd.date_range("2024-01-01", "2025-12-31")})
d["date_key"] = d["date"].dt.strftime("%Y%m%d").astype(int)
d["year"] = d["date"].dt.year
d["quarter"] = "Q" + d["date"].dt.quarter.astype(str)
d["month_num"] = d["date"].dt.month
d["month_name"] = d["date"].dt.strftime("%b")
d["year_month"] = d["date"].dt.strftime("%Y-%m")
d["weekday"] = d["date"].dt.strftime("%a")
d["is_weekend"] = d["date"].dt.dayofweek >= 5
d["season_event"] = "Regular"
d.loc[(d.date.dt.month == 11) & (d.date.dt.day == 11), "season_event"] = "11.11"
d.loc[(d.date.dt.month == 11) & (d.date.dt.day >= 24), "season_event"] = "Black Friday week"
d.loc[(d.date.dt.month == 12) & (d.date.dt.day >= 15), "season_event"] = "New Year sale"
d.loc[(d.date.dt.month == 3) & (d.date.dt.day <= 8), "season_event"] = "8 March"
d.to_csv(OUT / "dim_date.csv", index=False, date_format="%Y-%m-%d")

# customer dimension (+ RFM segment from the notebook, if available)
cust = customers.copy()
cust["age_2025"] = 2025 - cust["birth_year"]
cust["age_group"] = pd.cut(cust["age_2025"], [0, 24, 34, 44, 54, 120],
                           labels=["<25", "25-34", "35-44", "45-54", "55+"]).astype(str).replace("nan", "Unknown")
rfm_path = PROC / "rfm_segments.csv"
if rfm_path.exists():
    rfm = pd.read_csv(rfm_path)[["customer_id", "recency", "frequency", "monetary", "R", "F", "M", "segment"]]
    cust = cust.merge(rfm.rename(columns={"segment": "rfm_segment"}), on="customer_id", how="left")
    cust["rfm_segment"] = cust["rfm_segment"].fillna("No purchase")
cust.to_csv(OUT / "dim_customer.csv", index=False)

products.to_csv(OUT / "dim_product.csv", index=False)

dim_order = orders.copy()
dim_order["promo_code"] = dim_order["promo_code"].fillna("(none)")
dim_order["delivery_bucket"] = pd.cut(dim_order["delivery_days"], [0, 2, 4, 99],
                                      labels=["1-2 days", "3-4 days", "5+ days"]).astype(str).replace("nan", "n/a")
dim_order.drop(columns=["customer_id", "order_date"]).to_csv(OUT / "dim_order.csv", index=False)

for f in sorted(OUT.glob("*.csv")):
    print(f"{f.name:<18} {sum(1 for _ in open(f)) - 1:>7,} rows")
