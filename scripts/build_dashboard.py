"""
Build dashboard/index.html — a self-contained interactive dashboard
(no server, no external libraries; works on GitHub Pages).

Pre-aggregates the processed data into two small "cubes" and injects them
into scripts/dashboard_template.html.

Usage:  python scripts/build_dashboard.py
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"

customers = pd.read_csv(PROC / "customers.csv")
products = pd.read_csv(PROC / "products.csv")
orders = pd.read_csv(PROC / "orders.csv", parse_dates=["order_date"])
items = pd.read_csv(PROC / "order_items.csv")

o = orders.merge(customers[["customer_id", "city", "acquisition_channel"]], on="customer_id")
o = o.join(items.groupby("order_id")[["net_revenue", "cogs"]].sum(), on="order_id")
o["m"] = o["order_date"].dt.strftime("%Y-%m")
o["promo_code"] = o["promo_code"].fillna("(none)")
o["dl"] = o["status"] == "delivered"
o["net_d"] = o["net_revenue"].where(o["dl"], 0)
o["cogs_d"] = o["cogs"].where(o["dl"], 0)

cities = sorted(o["city"].unique(), key=lambda c: (c == "Unknown", c))
channels = customers["acquisition_channel"].value_counts().index.tolist()
promos = o["promo_code"].value_counts().index.tolist()
months = sorted(o["m"].unique())
cats = products["category"].unique().tolist()
idx = lambda lst: {v: i for i, v in enumerate(lst)}
CI, HI, PI, MI, KI = idx(cities), idx(channels), idx(promos), idx(months), idx(cats)

# order cube: month, city, channel, promo -> delivered orders, revenue, cogs, all orders,
#             returned orders, review sum, review count, delivery-day sum, slow(5+) orders
g = o.groupby(["m", "city", "acquisition_channel", "promo_code"]).agg(
    d=("dl", "sum"), rev=("net_d", "sum"), cogs=("cogs_d", "sum"), n=("order_id", "size"),
    ret=("status", lambda s: (s == "returned").sum()),
    rs=("review_score", "sum"), rc=("review_score", "count"),
    ds=("delivery_days", lambda s: s[o.loc[s.index, "dl"]].sum()),
).reset_index()
ocube = [[MI[r.m], CI[r.city], HI[r.acquisition_channel], PI[r.promo_code], int(r.d), round(r.rev), round(r.cogs),
          int(r.n), int(r.ret), int(r.rs), int(r.rc), int(r.ds)] for r in g.itertuples()]

# line cube: month, city, channel, category -> revenue, cogs (delivered only)
ln = (items.merge(o[["order_id", "m", "city", "acquisition_channel", "dl"]], on="order_id")
           .merge(products[["product_id", "category"]], on="product_id"))
ln = ln[ln["dl"]]
gl = ln.groupby(["m", "city", "acquisition_channel", "category"])[["net_revenue", "cogs"]].sum().reset_index()
lcube = [[MI[r.m], CI[r.city], HI[r.acquisition_channel], KI[r.category], round(r.net_revenue), round(r.cogs)]
         for r in gl.itertuples()]

data = {"months": months, "cities": cities, "channels": channels, "promos": promos, "cats": cats,
        "o": ocube, "l": lcube}
tpl = (ROOT / "scripts" / "dashboard_template.html").read_text()
html = tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
out = ROOT / "dashboard" / "index.html"
out.write_text(html)
print(f"wrote {out.relative_to(ROOT)}  ({len(html) / 1024:.0f} KB, {len(ocube)} + {len(lcube)} cube rows)")
