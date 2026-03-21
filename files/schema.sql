-- ============================================================
--  AgriStock Database Schema
--  Run this once to set up your MySQL database
--  Usage: mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS agristock;
USE agristock;

-- ── PRODUCTS ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    category      ENUM('Vegetable','Fruit','Dairy','Bakery','Grain','Other') DEFAULT 'Other',
    unit          VARCHAR(20)  DEFAULT 'kg',
    shelf_life    INT          DEFAULT 7,        -- days
    safety_stock  FLOAT        DEFAULT 30,
    reorder_qty   FLOAT        DEFAULT 60,
    sale_price    FLOAT        DEFAULT 0,
    waste_cost    FLOAT        DEFAULT 0,        -- cost per unit wasted
    stockout_cost FLOAT        DEFAULT 0,        -- cost per unit short
    holding_cost  FLOAT        DEFAULT 0.05,     -- cost per unit per day stored
    drought_factor FLOAT       DEFAULT 0.30,     -- fraction of normal supply in drought
    avg_supply    FLOAT        DEFAULT 100,      -- mean daily harvest
    supply_std    FLOAT        DEFAULT 15,       -- std dev of daily harvest
    demand_min    INT          DEFAULT 60,
    demand_max    INT          DEFAULT 120,
    location      VARCHAR(100) DEFAULT 'Warehouse',
    supplier      VARCHAR(100) DEFAULT '',
    active        TINYINT(1)   DEFAULT 1,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ── STOCK BATCHES ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stock_batches (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    product_id  INT NOT NULL,
    quantity    FLOAT NOT NULL,
    age_days    INT   DEFAULT 0,
    received_at DATE  DEFAULT (CURDATE()),
    expires_at  DATE,
    batch_note  VARCHAR(200) DEFAULT '',
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- ── TRANSACTIONS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    product_id     INT NOT NULL,
    txn_type       ENUM('sale','waste','delivery','stockout','reorder') NOT NULL,
    quantity       FLOAT NOT NULL,
    unit_price     FLOAT DEFAULT 0,
    total_value    FLOAT DEFAULT 0,
    party_name     VARCHAR(100) DEFAULT '',   -- supplier or buyer
    notes          VARCHAR(255) DEFAULT '',
    txn_date       DATE      DEFAULT (CURDATE()),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- ── DAILY SIMULATION LOG ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS sim_log (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    product_id  INT NOT NULL,
    sim_run_id  VARCHAR(50) NOT NULL,           -- groups one full run together
    day_num     INT NOT NULL,
    harvest     FLOAT DEFAULT 0,
    demand      FLOAT DEFAULT 0,
    sold        FLOAT DEFAULT 0,
    spoiled     FLOAT DEFAULT 0,
    stockout    FLOAT DEFAULT 0,
    stock_end   FLOAT DEFAULT 0,
    profit      FLOAT DEFAULT 0,
    drought     TINYINT(1) DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- ── ALERTS ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    product_id  INT,
    alert_type  ENUM('critical','warning','info','suggest') DEFAULT 'info',
    message     VARCHAR(500) NOT NULL,
    is_read     TINYINT(1) DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);

-- ── SEED DATA ────────────────────────────────────────────────
INSERT INTO products
  (name, category, unit, shelf_life, safety_stock, reorder_qty,
   sale_price, waste_cost, stockout_cost, holding_cost, drought_factor,
   avg_supply, supply_std, demand_min, demand_max, location, supplier)
VALUES
  ('Tomatoes',    'Vegetable','kg', 5,  30, 60,  35, 8,  15, 0.05, 0.30, 80, 15, 60, 110, 'Cold Room A', 'Farm Patel'),
  ('Strawberries','Fruit',    'kg', 3,  15, 40, 120,20,  50, 0.10, 0.15, 50, 18, 30,  80, 'Cold Room B', 'Berry Farm'),
  ('Spinach',     'Vegetable','kg', 4,  20, 35,  45,10,  25, 0.08, 0.20, 70, 20, 40,  90, 'Cold Room A', 'Green Fields'),
  ('Milk',        'Dairy',    'L',  7,  50,100,  52,12,  30, 0.05, 0.30,120, 18, 80, 130, 'Cold Room C', 'Dairy Co'),
  ('Bread',       'Bakery',   'pcs',2,  20, 50,  30, 9,  18, 0.04, 0.55, 50, 10, 30,  70, 'Shelf 1',     'City Bakery'),
  ('Potatoes',    'Vegetable','kg', 14, 60,120,  22, 5,  12, 0.03, 0.25,180, 25,120, 200, 'Dry Store',   'Farm Patel'),
  ('Mangoes',     'Fruit',    'kg', 6,  25, 70,  90,18,  40, 0.08, 0.20, 60, 20, 40,  90, 'Cold Room B', 'Mango Estate'),
  ('Wheat Flour', 'Grain',    'kg', 60, 80,200,  28, 4,  10, 0.02, 0.10,280, 30,200, 300, 'Dry Store',   'Mill Corp');

-- Seed some starting stock batches
INSERT INTO stock_batches (product_id, quantity, age_days, expires_at)
SELECT id, safety_stock, 2, DATE_ADD(CURDATE(), INTERVAL (shelf_life - 2) DAY)
FROM products;

-- Seed a few sample alerts
INSERT INTO alerts (product_id, alert_type, message)
VALUES
  (3, 'critical', 'Spinach expires in 1 day — only limited stock left'),
  (5, 'warning',  'Bread stock below safety level — reorder triggered'),
  (2, 'warning',  'Strawberries expiring in 2 days — consider applying discount'),
  (1, 'info',     'Tomato delivery received from Farm Patel'),
  (NULL,'suggest','Increase safety stock before upcoming festival season');
