"""
db.py  —  Database layer for AgriStock
Handles all MySQL queries. The UI never touches SQL directly.
"""

import mysql.connector
from mysql.connector import Error
import time
import math

# ─────────────────────────────────────────────
#  CONNECTION CONFIG  ← edit these
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "your_password",   # ← change this
    "database": "agristock",
    "autocommit": True,
}

# ─────────────────────────────────────────────
#  CONNECTION MANAGER
# ─────────────────────────────────────────────
_conn = None

def get_connection():
    global _conn
    try:
        if _conn and _conn.is_connected():
            return _conn
        _conn = mysql.connector.connect(**DB_CONFIG)
        return _conn
    except Error as e:
        raise ConnectionError(f"Cannot connect to MySQL: {e}")

def query(sql, params=(), fetch="all"):
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    if fetch == "all":
        result = cur.fetchall()
    elif fetch == "one":
        result = cur.fetchone()
    else:
        result = cur.lastrowid
    cur.close()
    return result

def execute(sql, params=()):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(sql, params)
    lid = cur.lastrowid
    cur.close()
    return lid

def executemany(sql, data):
    conn = get_connection()
    cur  = conn.cursor()
    cur.executemany(sql, data)
    cur.close()

# ─────────────────────────────────────────────
#  PRODUCTS
# ─────────────────────────────────────────────

def get_all_products():
    return query("SELECT * FROM products WHERE active=1 ORDER BY name")

def get_product(pid):
    return query("SELECT * FROM products WHERE id=%s", (pid,), fetch="one")

def update_product_thresholds(pid, safety, reorder, shelf):
    execute("""UPDATE products
               SET safety_stock=%s, reorder_qty=%s, shelf_life=%s
               WHERE id=%s""",
            (safety, reorder, shelf, pid))

def update_product_costs(pid, sale_price, waste_cost, stockout_cost, holding_cost):
    execute("""UPDATE products
               SET sale_price=%s, waste_cost=%s,
                   stockout_cost=%s, holding_cost=%s
               WHERE id=%s""",
            (sale_price, waste_cost, stockout_cost, holding_cost, pid))

def update_product_supply(pid, avg_supply, supply_std,
                          demand_min, demand_max, drought_factor):
    execute("""UPDATE products
               SET avg_supply=%s, supply_std=%s,
                   demand_min=%s, demand_max=%s,
                   drought_factor=%s
               WHERE id=%s""",
            (avg_supply, supply_std, demand_min, demand_max,
             drought_factor, pid))

def add_product(name, category, unit, shelf_life, safety_stock,
                reorder_qty, sale_price, waste_cost, stockout_cost,
                holding_cost, location, supplier):
    pid = execute("""INSERT INTO products
        (name,category,unit,shelf_life,safety_stock,reorder_qty,
         sale_price,waste_cost,stockout_cost,holding_cost,location,supplier)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (name,category,unit,shelf_life,safety_stock,reorder_qty,
         sale_price,waste_cost,stockout_cost,holding_cost,location,supplier))
    return pid

# ─────────────────────────────────────────────
#  STOCK BATCHES
# ─────────────────────────────────────────────

def get_stock_summary():
    """Returns one row per product with total qty and oldest batch age."""
    return query("""
        SELECT p.id, p.name, p.category, p.unit, p.shelf_life,
               p.safety_stock, p.reorder_qty, p.location, p.supplier,
               p.sale_price, p.waste_cost, p.stockout_cost,
               IFNULL(SUM(b.quantity),0)  AS total_qty,
               IFNULL(MAX(b.age_days),0)  AS max_age,
               IFNULL(MIN(b.expires_at), CURDATE()) AS nearest_expiry
        FROM products p
        LEFT JOIN stock_batches b ON b.product_id = p.id
        WHERE p.active = 1
        GROUP BY p.id
        ORDER BY p.name
    """)

def get_batches(pid):
    return query("""SELECT * FROM stock_batches
                    WHERE product_id=%s ORDER BY age_days DESC""", (pid,))

def add_batch(product_id, quantity, age_days=0, note=""):
    import datetime
    prod = get_product(product_id)
    shelf = prod["shelf_life"] if prod else 7
    expires = (datetime.date.today() +
               datetime.timedelta(days=shelf - age_days))
    execute("""INSERT INTO stock_batches
               (product_id, quantity, age_days, expires_at, batch_note)
               VALUES (%s,%s,%s,%s,%s)""",
            (product_id, quantity, age_days, expires, note))
    add_alert(product_id, "info",
              f"Delivery received: {quantity} {prod['unit']} of {prod['name']}")

def age_all_batches():
    """Call once daily — increments age and removes expired stock."""
    expired = query("""
        SELECT b.id, b.product_id, b.quantity, p.name, p.unit, p.waste_cost
        FROM stock_batches b
        JOIN products p ON p.id = b.product_id
        WHERE b.age_days >= p.shelf_life
    """)
    for row in expired:
        record_waste(row["product_id"], row["quantity"],
                     note="Auto-expired batch removed")
        execute("DELETE FROM stock_batches WHERE id=%s", (row["id"],))

    execute("UPDATE stock_batches SET age_days = age_days + 1")
    return len(expired)

def sell_stock(product_id, quantity, buyer="", price_override=None):
    """Sells from oldest batches first (FIFO)."""
    prod  = get_product(product_id)
    price = price_override if price_override else prod["sale_price"]
    remaining = quantity
    batches   = get_batches(product_id)

    for b in batches:
        if remaining <= 0: break
        take = min(b["quantity"], remaining)
        if b["quantity"] - take <= 0:
            execute("DELETE FROM stock_batches WHERE id=%s", (b["id"],))
        else:
            execute("UPDATE stock_batches SET quantity=quantity-%s WHERE id=%s",
                    (take, b["id"]))
        remaining -= take

    sold    = quantity - max(0, remaining)
    stockout= max(0, remaining)

    execute("""INSERT INTO transactions
               (product_id,txn_type,quantity,unit_price,total_value,party_name)
               VALUES (%s,'sale',%s,%s,%s,%s)""",
            (product_id, sold, price, sold * price, buyer))

    if stockout > 0:
        execute("""INSERT INTO transactions
                   (product_id,txn_type,quantity,notes)
                   VALUES (%s,'stockout',%s,'Demand exceeded stock')""",
                (product_id, stockout))
        add_alert(product_id, "warning",
                  f"Stockout: {stockout} {prod['unit']} of "
                  f"{prod['name']} unmet for {buyer}")
    return sold, stockout

def record_waste(product_id, quantity, note=""):
    prod = get_product(product_id)
    if not prod: return
    cost = quantity * prod["waste_cost"]
    execute("""INSERT INTO transactions
               (product_id,txn_type,quantity,total_value,notes)
               VALUES (%s,'waste',%s,%s,%s)""",
            (product_id, quantity, -cost, note))

def check_reorder(product_id):
    """Returns True and logs a reorder if stock is below safety level."""
    stock = get_stock_summary()
    row   = next((s for s in stock if s["id"] == product_id), None)
    if not row: return False
    prod  = get_product(product_id)
    if row["total_qty"] < prod["safety_stock"]:
        execute("""INSERT INTO transactions
                   (product_id,txn_type,quantity,notes)
                   VALUES (%s,'reorder',%s,'Auto reorder triggered')""",
                (product_id, prod["reorder_qty"]))
        add_alert(product_id, "warning",
                  f"Reorder triggered: {prod['reorder_qty']} "
                  f"{prod['unit']} of {prod['name']} ordered")
        return True
    return False

# ─────────────────────────────────────────────
#  TRANSACTIONS
# ─────────────────────────────────────────────

def get_recent_transactions(limit=50):
    return query("""
        SELECT t.*, p.name AS product_name, p.unit
        FROM transactions t
        JOIN products p ON p.id = t.product_id
        ORDER BY t.created_at DESC
        LIMIT %s
    """, (limit,))

def get_profit_summary():
    return query("""
        SELECT
          SUM(CASE WHEN txn_type='sale'     THEN total_value ELSE 0 END) AS revenue,
          SUM(CASE WHEN txn_type='waste'    THEN ABS(total_value) ELSE 0 END) AS waste_cost,
          SUM(CASE WHEN txn_type='stockout' THEN quantity ELSE 0 END) AS total_stockout,
          COUNT(CASE WHEN txn_type='sale'   THEN 1 END) AS sale_count
        FROM transactions
        WHERE txn_date = CURDATE()
    """, fetch="one")

def get_weekly_service_level():
    """Returns service % for each of the last 8 weeks."""
    return query("""
        SELECT
          YEARWEEK(txn_date,1) AS wk,
          SUM(CASE WHEN txn_type='sale'     THEN quantity ELSE 0 END) AS sold,
          SUM(CASE WHEN txn_type='stockout' THEN quantity ELSE 0 END) AS short
        FROM transactions
        WHERE txn_date >= DATE_SUB(CURDATE(), INTERVAL 8 WEEK)
        GROUP BY wk ORDER BY wk
    """)

def get_waste_by_product():
    return query("""
        SELECT p.name, SUM(t.quantity) AS total_waste
        FROM transactions t
        JOIN products p ON p.id = t.product_id
        WHERE t.txn_type='waste'
          AND t.txn_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY p.id ORDER BY total_waste DESC
    """)

# ─────────────────────────────────────────────
#  ALERTS
# ─────────────────────────────────────────────

def get_alerts(unread_only=False):
    sql = """SELECT a.*, p.name AS product_name
             FROM alerts a
             LEFT JOIN products p ON p.id = a.product_id
             ORDER BY a.created_at DESC LIMIT 100"""
    if unread_only:
        sql = sql.replace("ORDER BY", "WHERE a.is_read=0 ORDER BY")
    return query(sql)

def add_alert(product_id, alert_type, message):
    execute("""INSERT INTO alerts (product_id, alert_type, message)
               VALUES (%s,%s,%s)""",
            (product_id, alert_type, message))

def mark_alert_read(alert_id):
    execute("UPDATE alerts SET is_read=1 WHERE id=%s", (alert_id,))

def generate_expiry_alerts():
    """Auto-generate expiry alerts from current stock."""
    rows = query("""
        SELECT b.product_id, p.name, p.unit, p.shelf_life,
               b.age_days, b.quantity,
               (p.shelf_life - b.age_days) AS days_left
        FROM stock_batches b
        JOIN products p ON p.id = b.product_id
        WHERE (p.shelf_life - b.age_days) <= 3
    """)
    for r in rows:
        d = r["days_left"]
        atype = "critical" if d <= 1 else "warning"
        add_alert(r["product_id"], atype,
                  f"{r['name']}: {r['quantity']} {r['unit']} "
                  f"expires in {d} day{'s' if d!=1 else ''}")

# ─────────────────────────────────────────────
#  STOCHASTIC — OWN RNG (no import random)
# ─────────────────────────────────────────────
_seed = int(time.time() * 1000) % (2 ** 32)

def _rand():
    global _seed
    _seed = (1664525 * _seed + 1013904223) % (2 ** 32)
    return _seed / (2 ** 32)

def _sqrt(x):
    if x <= 0: return 0.0
    g = x / 2.0
    for _ in range(40): g = (g + x / g) / 2.0
    return g

def _ln(x):
    if x <= 0: return -700.0
    k = 0
    while x > 1.5: x /= 2.0; k += 1
    while x < 0.5: x *= 2.0; k -= 1
    y = (x - 1.0) / (x + 1.0)
    s, t = 0.0, y
    for n in range(1, 40, 2):
        s += t / n; t *= y * y
    return 2.0 * s + k * 0.6931471805599453

def _cos(x):
    PI = 3.14159265
    while x >  PI: x -= 2 * PI
    while x < -PI: x += 2 * PI
    s, t, sign = 0.0, 1.0, 1.0
    for n in range(1, 14):
        s += sign * t
        t *= x * x / ((2*n) * (2*n - 1))
        sign *= -1.0
    return s

def rand_gauss(mean, std):
    u1 = max(0.00001, _rand())
    u2 = _rand()
    z  = _sqrt(-2.0 * _ln(u1)) * _cos(2.0 * 3.14159265 * u2)
    return max(0.0, mean + std * z)

def rand_int_local(lo, hi):
    return lo + int(_rand() * (hi - lo + 1))

# ─────────────────────────────────────────────
#  STOCHASTIC SIMULATION ENGINE
# ─────────────────────────────────────────────

def simulate_one_day(stock, age, day, P, drought):
    factor  = P["drought_factor"] if drought else 1.0
    harvest = int(rand_gauss(P["avg_supply"] * factor,
                             P["supply_std"] * factor))
    demand  = rand_int_local(P["demand_min"], P["demand_max"])
    if day % 7 in (5, 6):
        demand = int(demand * 1.3)   # weekend surge

    stock += harvest
    age   += 1
    spoiled = 0
    if age >= P["shelf_life"]:
        spoiled = stock
        stock   = 0
        age     = 0

    sold      = min(stock, demand)
    stockout  = max(0, demand - stock)
    stock    -= sold

    safety = P["safety_stock"] * (1.8 if drought else 1.0)
    if stock < safety:
        stock += int(P["reorder_qty"] * (1.5 if drought else 1.0))

    revenue = sold    * P["sale_price"]
    w_cost  = spoiled * P["waste_cost"]
    s_cost  = stockout* P["stockout_cost"]
    h_cost  = stock   * P["holding_cost"]
    profit  = revenue - w_cost - s_cost - h_cost

    return stock, age, {
        "harvest":  harvest,  "demand":   demand,
        "sold":     sold,     "spoiled":  spoiled,
        "stockout": stockout, "stock":    stock,
        "profit":   round(profit, 2),
        "w_cost":   round(w_cost, 2),
        "s_cost":   round(s_cost, 2),
    }

def critical_ratio(P):
    cu = P["stockout_cost"]
    co = P["waste_cost"]
    if cu + co == 0: return 0.5
    return round(cu / (cu + co), 3)

def service_level(sold, demand):
    if demand == 0: return 100.0
    return round(sold / demand * 100, 1)

def waste_rate(spoiled, received):
    if received == 0: return 0.0
    return round(spoiled / received * 100, 1)

def run_monte_carlo(P, n_runs=300, days=None, drought=False,
                    progress_cb=None):
    """
    P         : product dict (from get_all_products row)
    n_runs    : number of independent simulations
    days      : simulation horizon (defaults to shelf_life * 10)
    drought   : whether to simulate drought conditions
    progress_cb: optional callback(pct) for progress bar
    Returns dict of aggregated statistics + raw lists.
    """
    global _seed
    if days is None:
        days = max(30, P["shelf_life"] * 10)

    profits, services, wastes, stockouts_list = [], [], [], []

    for r in range(n_runs):
        _seed = r * 7919 + 1
        stock = P["safety_stock"]
        age   = 0
        t_profit = t_sold = t_demand = t_spoiled = t_stockout = 0
        t_received = P["safety_stock"]

        for day in range(1, days + 1):
            stock, age, res = simulate_one_day(stock, age, day, P, drought)
            t_profit   += res["profit"]
            t_sold     += res["sold"]
            t_demand   += res["demand"]
            t_spoiled  += res["spoiled"]
            t_stockout += res["stockout"]
            t_received += res["harvest"]

        profits.append(round(t_profit, 2))
        services.append(service_level(t_sold, t_demand))
        wastes.append(waste_rate(t_spoiled, t_received))
        stockouts_list.append(t_stockout)

        if progress_cb:
            progress_cb(int((r + 1) / n_runs * 100))

    def avg(lst): return round(sum(lst) / len(lst), 2)
    def _sd(lst):
        m = avg(lst)
        return round(_sqrt(sum((x - m) ** 2 for x in lst) / len(lst)), 2)

    return {
        "profits":      profits,
        "services":     services,
        "wastes":       wastes,
        "stockouts":    stockouts_list,
        "p_avg":        avg(profits),
        "p_std":        _sd(profits),
        "p_best":       max(profits),
        "p_worst":      min(profits),
        "svc_avg":      avg(services),
        "svc_std":      _sd(services),
        "wst_avg":      avg(wastes),
        "wst_std":      _sd(wastes),
        "cr":           critical_ratio(P),
        "days":         days,
        "n_runs":       n_runs,
    }

def run_what_if(P, n_runs=200):
    """Compare normal vs drought — returns both sets of results."""
    normal  = run_monte_carlo(P, n_runs=n_runs, drought=False)
    drought_r = run_monte_carlo(P, n_runs=n_runs, drought=True)
    return {
        "normal":  normal,
        "drought": drought_r,
        "profit_loss": round(normal["p_avg"] - drought_r["p_avg"], 2),
        "svc_drop":    round(normal["svc_avg"] - drought_r["svc_avg"], 1),
        "waste_rise":  round(drought_r["wst_avg"] - normal["wst_avg"], 1),
    }

def optimal_safety_stock(P, target_service=0.95, n_runs=100):
    """
    Binary-search the safety stock that achieves target_service level.
    Returns the recommended safety stock quantity.
    """
    lo, hi = 0, int(P["avg_supply"] * 3)
    best   = P["safety_stock"]
    for _ in range(12):
        mid = (lo + hi) // 2
        test_P = dict(P, safety_stock=mid)
        res = run_monte_carlo(test_P, n_runs=n_runs)
        if res["svc_avg"] / 100 >= target_service:
            best = mid
            hi   = mid - 1
        else:
            lo   = mid + 1
    return best

def save_sim_results_to_db(product_id, run_id, daily_log):
    """
    daily_log: list of dicts from simulate_one_day
    Saves to sim_log table for historical analysis.
    """
    rows = [
        (product_id, run_id, i+1,
         d["harvest"], d["demand"], d["sold"],
         d["spoiled"], d["stockout"], d["stock"], d["profit"], 0)
        for i, d in enumerate(daily_log)
    ]
    executemany("""
        INSERT INTO sim_log
          (product_id,sim_run_id,day_num,harvest,demand,sold,
           spoiled,stockout,stock_end,profit,drought)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, rows)

def get_sim_history(product_id, limit=5):
    return query("""
        SELECT sim_run_id,
               COUNT(*)          AS days,
               SUM(profit)       AS total_profit,
               SUM(spoiled)      AS total_spoiled,
               SUM(stockout)     AS total_stockout,
               MIN(created_at)   AS run_date
        FROM sim_log
        WHERE product_id=%s
        GROUP BY sim_run_id
        ORDER BY run_date DESC
        LIMIT %s
    """, (product_id, limit))
