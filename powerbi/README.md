# Power BI / Tableau kit

Everything you need to rebuild the dashboard in Power BI Desktop or Tableau Public:
a clean **star schema** in `model/`, ready-made **DAX measures** in `measures.dax`,
and a page-by-page **report spec** below.

## Data model

```
                 dim_date (date_key)
                        │ 1
                        │
dim_customer ──1──*  fact_sales  *──1── dim_product
 (customer_id)      (order line)        (product_id)
                        │ *
                        │
                        1
                 dim_order (order_id)
```

| Table | Grain | Rows | Key columns |
|---|---|---|---|
| `fact_sales` | one order line | 40,448 | `order_item_id`, `order_id`, `date_key`, `customer_id`, `product_id`, revenue/cost columns |
| `dim_date` | one day (2024–2025) | 731 | `date_key`, `date`, year, quarter, month, weekday, `season_event` |
| `dim_customer` | one customer | 12,000 | city, gender, `age_group`, `acquisition_channel`, RFM scores + `rfm_segment` |
| `dim_product` | one product | 160 | category, brand, unit price/cost |
| `dim_order` | one order | 26,341 | status, payment method, promo code, delivery days/bucket, review score |

## Power BI — setup (≈10 minutes)

1. **Get data ▸ Text/CSV**, load the five files from `model/`.
2. **Model view**: create the relationships in the diagram above (many-to-one, from `fact_sales`).
   Set `fact_sales ↔ dim_order` cross-filter direction to **Both** — this lets date/category
   slicers filter the review-score measures that live on `dim_order`.
3. Select `dim_date` ▸ **Mark as date table** ▸ column `date`.
4. Sort `dim_date[month_name]` by `month_num`.
5. **New measure** ▸ paste measures from `measures.dax` one by one
   (or put them in a dedicated `_Measures` table).
6. Format: `Net Revenue`, `Gross Profit`, `AOV` as whole numbers with thousands separator (KZT);
   all `%` measures as Percentage, 1 decimal.

## Suggested report (3 pages)

**Page 1 — Executive overview**
- KPI cards: Net Revenue, Revenue YoY %, Gross Margin %, Orders, AOV, Return Rate %
- Line chart: Net Revenue by `year_month` (or month_name with `year` as legend)
- Bar chart: Net Revenue by `category`, tooltip with Gross Margin %
- Slicers (one row, top): year, city, acquisition_channel

**Page 2 — Customers**
- Bar: Profit per Registered Customer by `acquisition_channel`
- Bar: Return Rate % by `acquisition_channel`
- Treemap or bar: Active Customers and Net Revenue by `rfm_segment`
- Matrix: cohort (first-order quarter) × quarter — optional stretch goal

**Page 3 — Operations & promotions**
- Column: Avg Review and Low Review % by `delivery_bucket`
- Map / bar: Net Revenue and avg delivery days by `city`
- Bar: Gross Margin % by `promo_code` with a reference line at the full-price margin

Expected values for checking your build (both years): Net Revenue ≈ **4.11 bn KZT**,
Gross Margin ≈ **18.0%**, 2025 YoY ≈ **+53%**, Return Rate ≈ **7.0%**.

## Tableau

Use the same CSVs. In **Data Source**, drag `fact_sales` first, then relate the four dimensions
on their keys (Tableau relationships, not joins). Equivalent calculated fields:

```text
Net Revenue      = SUM(IF [status] = "delivered" THEN [net_revenue] END)
Gross Profit     = SUM(IF [status] = "delivered" THEN [net_revenue] - [cogs] END)
Gross Margin %   = [Gross Profit] / [Net Revenue]
Orders           = COUNTD(IF [status] = "delivered" THEN [order_id] END)
AOV              = [Net Revenue] / [Orders]
Return Rate %    = COUNTD(IF [status] = "returned" THEN [order_id] END) / COUNTD([order_id])
```

Publish to Tableau Public and link it from the main README.
