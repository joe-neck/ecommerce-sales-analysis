"""
Generate a realistic (synthetic) e-commerce dataset for "Dala Market",
a fictional online electronics & home-tech store operating in Kazakhstan.

Period: 2024-01-01 .. 2025-12-31. Prices are in KZT (Kazakhstani tenge).

The raw files intentionally contain a few real-world data-quality issues
(duplicate rows, inconsistent city spellings, missing values, impossible
birth years) so the cleaning step has something to do.

Usage:  python scripts/generate_data.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2024-01-01")
END = pd.Timestamp("2025-12-31")
DAYS = (END - START).days + 1
N_CUSTOMERS = 12_000

# --------------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------------
CITIES = {  # city: (share of customers, base delivery days)
    "Almaty": (0.29, 1), "Astana": (0.22, 1), "Shymkent": (0.10, 2),
    "Karaganda": (0.07, 3), "Aktobe": (0.05, 3), "Atyrau": (0.05, 4),
    "Pavlodar": (0.04, 3), "Ust-Kamenogorsk": (0.04, 4), "Kostanay": (0.04, 3),
    "Taraz": (0.04, 3), "Aktau": (0.03, 5), "Kyzylorda": (0.03, 4),
}
CHANNELS = {  # channel: (share, extra-orders lambda, return-rate uplift)
    "Organic Search": (0.24, 1.9, 0.00),
    "Paid Search":    (0.20, 1.2, 0.01),
    "Instagram":      (0.18, 1.1, 0.02),
    "TikTok":         (0.13, 0.6, 0.05),
    "Email":          (0.10, 2.6, 0.00),
    "Referral":       (0.15, 2.3, -0.01),
}
CATEGORIES = {  # category: (price range KZT, margin range, base weight, return uplift)
    "Smartphones":     ((90_000, 650_000), (0.10, 0.18), 0.17, 0.02),
    "Laptops":         ((220_000, 900_000), (0.08, 0.15), 0.09, 0.04),
    "Audio":           ((9_000, 180_000), (0.25, 0.40), 0.16, 0.01),
    "Home Appliances": ((25_000, 450_000), (0.18, 0.30), 0.14, 0.02),
    "Smart Home":      ((7_000, 120_000), (0.30, 0.45), 0.10, 0.00),
    "Accessories":     ((2_500, 35_000), (0.40, 0.60), 0.20, -0.02),
    "Gaming":          ((15_000, 350_000), (0.15, 0.28), 0.07, 0.01),
    "Beauty Tech":     ((12_000, 220_000), (0.28, 0.42), 0.07, 0.01),
}
BRANDS = {
    "Smartphones": ["Samsung", "Apple", "Xiaomi", "Honor", "Realme"],
    "Laptops": ["Lenovo", "ASUS", "HP", "Apple", "Acer"],
    "Audio": ["JBL", "Sony", "Apple", "Marshall", "Xiaomi"],
    "Home Appliances": ["Philips", "Bosch", "Tefal", "Dyson", "Midea"],
    "Smart Home": ["Xiaomi", "TP-Link", "Yandex", "Aqara", "Tuya"],
    "Accessories": ["Anker", "Baseus", "Ugreen", "Samsung", "Xiaomi"],
    "Gaming": ["Sony", "Logitech", "HyperX", "Razer", "Nintendo"],
    "Beauty Tech": ["Philips", "Dyson", "Braun", "Rowenta", "Xiaomi"],
}
ITEM_WORDS = {
    "Smartphones": ["Phone", "Phone Pro", "Phone Lite", "Phone Max", "Phone Mini"],
    "Laptops": ["Notebook 14", "Notebook 15", "Ultrabook", "Gaming Laptop", "2-in-1"],
    "Audio": ["Wireless Earbuds", "Headphones", "Bluetooth Speaker", "Soundbar", "Neckband"],
    "Home Appliances": ["Vacuum Cleaner", "Air Fryer", "Coffee Machine", "Blender", "Air Purifier"],
    "Smart Home": ["Smart Bulb", "Smart Plug", "Wi-Fi Camera", "Smart Speaker", "Door Sensor"],
    "Accessories": ["USB-C Cable", "Power Bank", "Phone Case", "Charger 65W", "Screen Protector"],
    "Gaming": ["Console", "Gamepad", "Gaming Mouse", "Gaming Headset", "Keyboard"],
    "Beauty Tech": ["Hair Dryer", "Trimmer", "Styler", "Electric Toothbrush", "Epilator"],
}
# Month-level demand multipliers (11.11 + Black Friday, New Year, 8 March)
MONTH_SEASON = {1: 0.80, 2: 0.85, 3: 1.05, 4: 0.90, 5: 0.90, 6: 0.85,
                7: 0.85, 8: 0.95, 9: 1.00, 10: 1.00, 11: 1.55, 12: 1.45}
# Category tilts by month
CATEGORY_SEASON = {
    3: {"Beauty Tech": 2.2, "Audio": 1.2},
    8: {"Laptops": 1.8, "Accessories": 1.2},  # back to school
    9: {"Laptops": 1.6, "Smartphones": 1.3},  # new phone launches
    11: {"Home Appliances": 1.6, "Smartphones": 1.2, "Gaming": 1.3},
    12: {"Gaming": 1.8, "Audio": 1.4, "Smart Home": 1.3},
}


def day_weight(d: pd.Timestamp) -> float:
    """Demand weight for a calendar day: trend x season x weekday x promo days."""
    trend = 1.0 + 0.40 * ((d - START).days / DAYS)          # ~40% growth over 2y
    w = trend * MONTH_SEASON[d.month]
    w *= [1.0, 0.98, 0.97, 1.0, 1.05, 1.12, 1.08][d.dayofweek]
    if d.month == 11 and d.day == 11:
        w *= 3.0                                              # 11.11
    if d.month == 11 and d.day >= 24:
        w *= 1.8                                              # Black Friday week
    if d.month == 3 and 1 <= d.day <= 7:
        w *= 1.6                                              # before 8 March
    if d.month == 12 and 15 <= d.day <= 30:
        w *= 1.4                                              # New Year gifts
    if d.month == 1 and d.day <= 7:
        w *= 0.6                                              # holidays lull
    return w


calendar = pd.date_range(START, END, freq="D")
cal_w = np.array([day_weight(d) for d in calendar])
cal_p = cal_w / cal_w.sum()
CUM = np.cumsum(cal_w / cal_w.mean())  # seasonal clock for repeat purchases

# --------------------------------------------------------------------------
# Products
# --------------------------------------------------------------------------
products = []
pid = 1
for cat, (prange, mrange, _, _) in CATEGORIES.items():
    for brand in BRANDS[cat]:
        for word in rng.choice(ITEM_WORDS[cat], size=4, replace=False):
            lo, hi = prange
            price = float(np.exp(rng.uniform(np.log(lo), np.log(hi))))
            price = round(price / 1000) * 1000 - 10  # e.g. 149 990
            margin = rng.uniform(*mrange)
            model = rng.integers(2, 20)
            products.append({
                "product_id": f"P{pid:04d}",
                "product_name": f"{brand} {word} {model}",
                "category": cat,
                "brand": brand,
                "unit_price": price,
                "unit_cost": round(price * (1 - margin), 0),
            })
            pid += 1
products = pd.DataFrame(products)
# popularity: zipf-like within category, cheaper items slightly more popular
products["popularity"] = rng.zipf(1.6, len(products)).clip(1, 40) / np.log(products["unit_price"])

# --------------------------------------------------------------------------
# Customers
# --------------------------------------------------------------------------
city_names = list(CITIES)
city_p = np.array([v[0] for v in CITIES.values()]); city_p /= city_p.sum()
ch_names = list(CHANNELS)
ch_p = np.array([v[0] for v in CHANNELS.values()]); ch_p /= ch_p.sum()

signup_idx = rng.choice(DAYS, size=N_CUSTOMERS, p=cal_p)
customers = pd.DataFrame({
    "customer_id": [f"C{i:05d}" for i in range(1, N_CUSTOMERS + 1)],
    "signup_date": calendar[signup_idx],
    "city": rng.choice(city_names, size=N_CUSTOMERS, p=city_p),
    "gender": rng.choice(["F", "M"], size=N_CUSTOMERS, p=[0.52, 0.48]),
    "birth_year": rng.normal(1993, 9, N_CUSTOMERS).round().clip(1955, 2007).astype(int),
    "acquisition_channel": rng.choice(ch_names, size=N_CUSTOMERS, p=ch_p),
})
# TikTok skews younger
tt = customers["acquisition_channel"] == "TikTok"
customers.loc[tt, "birth_year"] = rng.normal(2000, 4, tt.sum()).round().clip(1980, 2007).astype(int)
customers = customers.sort_values("signup_date").reset_index(drop=True)
customers["customer_id"] = [f"C{i:05d}" for i in range(1, N_CUSTOMERS + 1)]

# --------------------------------------------------------------------------
# Orders
# --------------------------------------------------------------------------
cats = list(CATEGORIES)
orders, items = [], []
oid, iid = 1, 1
payment_methods = ["QR payment", "Bank card", "Installments 0-0-12", "Cash on delivery"]

for c in customers.itertuples(index=False):
    lam = CHANNELS[c.acquisition_channel][1]
    n_orders = 1 + rng.poisson(lam)
    d = c.signup_date + pd.Timedelta(days=int(rng.integers(0, 3)))
    dates = []
    for k in range(n_orders):
        if k > 0:
            # gap to next purchase measured in "seasonal time": busy periods
            # (Nov, Dec, March) pass faster, so repeat orders cluster there
            pos = CUM[(d - START).days] + rng.exponential(85) + 7
            j = int(np.searchsorted(CUM, pos))
            if j >= DAYS:
                break
            d = calendar[j]
        if d > END:
            break
        dates.append(d)

    for od in dates:
        m = od.month
        # basket
        n_items = rng.choice([1, 2, 3, 4], p=[0.62, 0.26, 0.09, 0.03])
        cat_w = np.array([CATEGORIES[k][2] * CATEGORY_SEASON.get(m, {}).get(k, 1.0) for k in cats])
        cat_w /= cat_w.sum()
        promo = None
        disc = 0.0
        if m == 11 and (od.day == 11 or od.day >= 24):
            promo, disc = ("SALE1111" if od.day == 11 else "BLACKFRIDAY"), rng.choice([0.10, 0.15, 0.20, 0.25])
        elif m == 12 and od.day >= 15:
            promo, disc = "NEWYEAR", rng.choice([0.05, 0.10, 0.15])
        elif m == 3 and od.day <= 8:
            promo, disc = "MARCH8", rng.choice([0.10, 0.15])
        elif rng.random() < 0.07:
            promo, disc = "WELCOME5", 0.05

        order_cats = []
        for _ in range(n_items):
            cat = rng.choice(cats, p=cat_w)
            pool = products[products["category"] == cat]
            pw = pool["popularity"].to_numpy(); pw = pw / pw.sum()
            prow = pool.iloc[rng.choice(len(pool), p=pw)]
            qty = 1 if prow.unit_price > 60_000 else int(rng.choice([1, 1, 1, 2, 3]))
            items.append({
                "order_item_id": iid, "order_id": f"O{oid:06d}",
                "product_id": prow.product_id, "quantity": qty,
                "unit_price": prow.unit_price, "discount_pct": disc,
            })
            order_cats.append(cat)
            iid += 1

        # delivery & status
        base = CITIES[c.city][1]
        peak = 2 if m in (11, 12) else 0
        delivery = int(base + rng.poisson(0.8) + rng.integers(0, peak + 1))
        p_return = 0.045 + CHANNELS[c.acquisition_channel][2] + max(CATEGORIES[k][3] for k in order_cats)
        p_return += 0.03 if delivery >= 5 else 0
        r = rng.random()
        status = "cancelled" if r < 0.03 else ("returned" if r < 0.03 + p_return else "delivered")

        # review score: driven by delivery speed and status
        review = np.nan
        if status != "cancelled" and rng.random() < 0.65:
            mu = 4.7 if delivery <= 2 else (4.3 if delivery <= 4 else 3.5)
            if status == "returned":
                mu -= 1.6
            review = int(np.clip(round(rng.normal(mu, 0.8)), 1, 5))

        orders.append({
            "order_id": f"O{oid:06d}", "customer_id": c.customer_id,
            "order_date": od.strftime("%Y-%m-%d"), "status": status,
            "payment_method": rng.choice(payment_methods, p=[0.46, 0.30, 0.17, 0.07]),
            "delivery_days": delivery if status != "cancelled" else np.nan,
            "review_score": review, "promo_code": promo,
        })
        oid += 1

orders = pd.DataFrame(orders).sort_values(["order_date", "order_id"]).reset_index(drop=True)
items = pd.DataFrame(items)
# re-number orders chronologically
id_map = {old: f"O{i:06d}" for i, old in enumerate(orders["order_id"], start=1)}
orders["order_id"] = orders["order_id"].map(id_map)
items["order_id"] = items["order_id"].map(id_map)
items = items.sort_values(["order_id", "order_item_id"]).reset_index(drop=True)
items["order_item_id"] = np.arange(1, len(items) + 1)
orders["delivery_days"] = orders["delivery_days"].astype("Int64")
orders["review_score"] = orders["review_score"].astype("Int64")
products["unit_cost"] = products["unit_cost"].astype(int)
products["unit_price"] = products["unit_price"].astype(int)
items["unit_price"] = items["unit_price"].astype(int)

# --------------------------------------------------------------------------
# Inject realistic data-quality issues into RAW files
# --------------------------------------------------------------------------
cust_raw = customers.copy()
cust_raw["signup_date"] = cust_raw["signup_date"].dt.strftime("%Y-%m-%d")
idx = rng.choice(len(cust_raw), 400, replace=False)
variants = {"Astana": ["Nur-Sultan", "astana", "ASTANA "], "Almaty": ["almaty", " Almaty", "ALMATY"],
            "Shymkent": ["Shimkent"], "Ust-Kamenogorsk": ["Oskemen", "Ust Kamenogorsk"],
            "Karaganda": ["Karagandy"]}
for i in idx:
    city = cust_raw.at[i, "city"]
    if city in variants:
        cust_raw.at[i, "city"] = rng.choice(variants[city])
cust_raw.loc[rng.choice(len(cust_raw), 110, replace=False), "city"] = np.nan
cust_raw.loc[rng.choice(len(cust_raw), 15, replace=False), "birth_year"] = rng.choice([1900, 1901, 2019, 2021], 15)
cust_raw = pd.concat([cust_raw, cust_raw.sample(25, random_state=SEED)]).reset_index(drop=True)  # dupes

items_raw = pd.concat([items, items.sample(180, random_state=SEED)]).sort_values("order_item_id").reset_index(drop=True)

cust_raw.to_csv(RAW / "customers.csv", index=False)
products.drop(columns="popularity").to_csv(RAW / "products.csv", index=False)
orders.to_csv(RAW / "orders.csv", index=False)
items_raw.to_csv(RAW / "order_items.csv", index=False)

print(f"customers:   {len(cust_raw):>7,}")
print(f"products:    {len(products):>7,}")
print(f"orders:      {len(orders):>7,}")
print(f"order_items: {len(items_raw):>7,}")
