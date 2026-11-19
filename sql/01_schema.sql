-- Dala Market e-commerce database (SQLite)
-- Created by scripts/clean_data.py

CREATE TABLE customers (
    customer_id         TEXT PRIMARY KEY,
    signup_date         DATE NOT NULL,
    city                TEXT NOT NULL,
    gender              TEXT,
    birth_year          INTEGER,
    acquisition_channel TEXT NOT NULL
);

CREATE TABLE products (
    product_id   TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category     TEXT NOT NULL,
    brand        TEXT NOT NULL,
    unit_price   INTEGER NOT NULL,   -- KZT
    unit_cost    INTEGER NOT NULL    -- KZT
);

CREATE TABLE orders (
    order_id       TEXT PRIMARY KEY,
    customer_id    TEXT NOT NULL REFERENCES customers(customer_id),
    order_date     DATE NOT NULL,
    status         TEXT NOT NULL CHECK (status IN ('delivered','returned','cancelled')),
    payment_method TEXT,
    delivery_days  INTEGER,
    review_score   INTEGER CHECK (review_score BETWEEN 1 AND 5),
    promo_code     TEXT
);

CREATE TABLE order_items (
    order_item_id   INTEGER PRIMARY KEY,
    order_id        TEXT NOT NULL REFERENCES orders(order_id),
    product_id      TEXT NOT NULL REFERENCES products(product_id),
    quantity        INTEGER NOT NULL,
    unit_price      INTEGER NOT NULL,
    discount_pct    REAL NOT NULL DEFAULT 0,
    gross_revenue   REAL NOT NULL,
    discount_amount REAL NOT NULL,
    net_revenue     REAL NOT NULL,
    cogs            REAL NOT NULL
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date     ON orders(order_date);
CREATE INDEX idx_items_order     ON order_items(order_id);
CREATE INDEX idx_items_product   ON order_items(product_id);

-- Convenience view: one row per completed (delivered) order line
CREATE VIEW v_sales AS
SELECT  oi.*, o.customer_id, o.order_date, o.status, o.promo_code,
        p.category, p.brand, c.city, c.acquisition_channel
FROM order_items oi
JOIN orders    o ON o.order_id   = oi.order_id
JOIN products  p ON p.product_id = oi.product_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.status = 'delivered';
