# =============================================================
#  STOCHASTIC PERISHABLE INVENTORY MANAGEMENT
#  Fresh Produce Hub Simulator
#
#  Run with:  python main.py
#  No external libraries used. Not even "import random".
#
#  WHAT THIS PROGRAM DOES:
#  Every day, two random things happen:
#    1. Farm sends a random amount of produce  (SUPPLY)
#    2. Customers buy a random amount          (DEMAND)
#  We track stock, spoilage, profit, and key metrics.
#  We can trigger a DROUGHT to see how inventory survives.
#  Monte Carlo runs 300 simulations to show risk distribution.
# =============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import time


# =============================================================
#  SECTION 1 — OUR OWN RANDOM NUMBER GENERATOR
#  (We do NOT use "import random")
#
#  Algorithm: Linear Congruential Generator (LCG)
#  Formula  : next = (A × state + C) % M
#  This is exactly how Python's built-in random works inside.
#  A, C, M are special constants that give a good spread.
# =============================================================

_seed = int(time.time() * 1000) % (2 ** 32)   # start from clock

def _rand():
    """Generates one random float between 0.0 and 1.0"""
    global _seed
    _seed = (1664525 * _seed + 1013904223) % (2 ** 32)
    return _seed / (2 ** 32)

def rand_int(lo, hi):
    """Random whole number from lo to hi (inclusive)"""
    return lo + int(_rand() * (hi - lo + 1))

def rand_gauss(mean, std):
    """
    Random number from a bell curve (Normal distribution).
    Uses Box-Muller Transform:
      z = sqrt(-2 × ln(u1)) × cos(2π × u2)
    We build sqrt, ln, cos ourselves — no math library needed.
    """
    u1 = max(0.00001, _rand())
    u2 = _rand()
    z  = _sqrt(-2.0 * _ln(u1)) * _cos(2.0 * 3.14159265 * u2)
    return max(0.0, mean + std * z)

# -- Math helpers (built from scratch) ------------------------

def _sqrt(x):
    """Square root using Newton-Raphson: guess = (guess + x/guess) / 2"""
    if x <= 0: return 0.0
    g = x / 2.0
    for _ in range(40):
        g = (g + x / g) / 2.0
    return g

def _ln(x):
    """Natural logarithm using series expansion"""
    if x <= 0: return -700.0
    k = 0
    while x > 1.5: x /= 2.0; k += 1
    while x < 0.5: x *= 2.0; k -= 1
    y = (x - 1.0) / (x + 1.0)
    s, t = 0.0, y
    for n in range(1, 40, 2):
        s += t / n
        t *= y * y
    return 2.0 * s + k * 0.6931471805599453

def _cos(x):
    """Cosine using Taylor series: 1 - x²/2! + x⁴/4! - ..."""
    PI = 3.14159265
    while x >  PI: x -= 2 * PI
    while x < -PI: x += 2 * PI
    s, t, sign = 0.0, 1.0, 1.0
    for n in range(1, 14):
        s += sign * t
        t *= x * x / ((2*n) * (2*n - 1))
        sign *= -1.0
    return s


# =============================================================
#  SECTION 2 — PRODUCT PRESETS
#  Four real agricultural products with realistic numbers.
#  Each has its own shelf life, supply, demand, and costs.
# =============================================================

PRODUCTS = {
    "🥛  Milk  (7-day shelf life)": {
        "shelf": 7,   "sup": 120, "std": 18,
        "dmin":  80,  "dmax": 130,
        "ss":    70,  "oq":  100,
        "price": 3.5, "wcost": 1.2, "scost": 2.5, "hcost": 0.05,
        "dfact": 0.30, "days": 60,
    },
    "🍓  Strawberries  (3-day shelf life)": {
        "shelf": 3,   "sup": 60,  "std": 20,
        "dmin":  40,  "dmax": 90,
        "ss":    40,  "oq":  70,
        "price": 8.0, "wcost": 2.0, "scost": 5.0, "hcost": 0.10,
        "dfact": 0.15, "days": 45,
    },
    "🥬  Leafy Greens  (4-day shelf life)": {
        "shelf": 4,   "sup": 80,  "std": 22,
        "dmin":  50,  "dmax": 100,
        "ss":    55,  "oq":  90,
        "price": 4.5, "wcost": 1.5, "scost": 3.0, "hcost": 0.08,
        "dfact": 0.20, "days": 60,
    },
    "🍞  Bread  (2-day shelf life)": {
        "shelf": 2,   "sup": 50,  "std": 10,
        "dmin":  30,  "dmax": 70,
        "ss":    35,  "oq":  60,
        "price": 2.5, "wcost": 0.9, "scost": 1.8, "hcost": 0.04,
        "dfact": 0.55, "days": 45,
    },
}


# =============================================================
#  SECTION 3 — ONE DAY OF SIMULATION
#  This is the heart of the project.
#  Call this once per day. It returns everything that happened.
#
#  Inputs : stock, age, day number, parameters, drought flag
#  Returns: new stock, new age, dict of results
# =============================================================

def simulate_one_day(stock, age, day, P, drought):
    """
    Simulates one day at the Fresh Produce Hub.

    STEP 1: Farm sends produce today (supply)
    STEP 2: Customers arrive and want to buy (demand)
    STEP 3: Add supply to warehouse
    STEP 4: Check if stock has expired (spoilage)
    STEP 5: Sell to customers
    STEP 6: Reorder if stock is running low
    STEP 7: Calculate today's profit
    """

    # STEP 1 — SUPPLY
    # Normal day: harvest follows a bell curve around the mean.
    # Drought day: harvest is only dfact% of normal (e.g. 30%).
    factor  = P["dfact"] if drought else 1.0
    harvest = int(rand_gauss(P["sup"] * factor, P["std"] * factor))

    # STEP 2 — DEMAND
    # Random number of customers between dmin and dmax.
    # Weekends (day 5 and 6 of the week) are 30% busier.
    demand = rand_int(P["dmin"], P["dmax"])
    if day % 7 in (5, 6):
        demand = int(demand * 1.3)   # weekend surge

    # STEP 3 — ADD SUPPLY TO WAREHOUSE
    stock += harvest

    # STEP 4 — SPOILAGE CHECK
    # Stock gets 1 day older every day.
    # Once it hits shelf_life, EVERYTHING expires → total loss.
    age    += 1
    spoiled = 0
    if age >= P["shelf"]:
        spoiled = stock   # all stock is wasted
        stock   = 0
        age     = 0       # fresh start after clear-out

    # STEP 5 — SELL
    sold     = min(stock, demand)       # can't sell more than we have
    stockout = max(0, demand - stock)   # unmet demand = lost customers
    stock   -= sold

    # STEP 6 — REORDER
    # If stock drops below safety stock → place an order.
    # During drought: raise safety stock by 80%, order 50% more.
    # This is the DROUGHT DEFENCE strategy.
    safety = P["ss"] * (1.8 if drought else 1.0)
    if stock < safety:
        stock += int(P["oq"] * (1.5 if drought else 1.0))

    # STEP 7 — PROFIT
    # Revenue from sales, minus cost of waste, stockouts, and holding.
    revenue  = sold     * P["price"]    # money earned
    w_cost   = spoiled  * P["wcost"]    # loss from expired stock
    s_cost   = stockout * P["scost"]    # penalty for missing customers
    h_cost   = stock    * P["hcost"]    # cost of storing unsold stock
    profit   = revenue - w_cost - s_cost - h_cost

    return stock, age, {
        "harvest":  harvest,
        "demand":   demand,
        "sold":     sold,
        "spoiled":  spoiled,
        "stockout": stockout,
        "stock":    stock,
        "profit":   round(profit, 2),
        "w_cost":   round(w_cost, 2),
        "s_cost":   round(s_cost, 2),
    }


# =============================================================
#  SECTION 4 — KEY PERFORMANCE INDICATORS (KPIs)
#
#  Service Level  = What % of customer demand was fulfilled?
#                   Formula: (total sold / total demand) × 100
#
#  Waste Rate     = What % of received produce was wasted?
#                   Formula: (total spoiled / total received) × 100
#
#  Critical Ratio = The theoretical "sweet spot" for ordering.
#                   Formula: Cu / (Cu + Co)
#                   Cu = cost per unit of stockout (shortage cost)
#                   Co = cost per unit of waste
#                   If CR is high → keep more stock (shortage is worse)
#                   If CR is low  → keep less stock (waste is worse)
# =============================================================

def service_level(sold, demand):
    if demand == 0: return 100.0
    return round(sold / demand * 100, 1)

def waste_rate(spoiled, received):
    if received == 0: return 0.0
    return round(spoiled / received * 100, 1)

def critical_ratio(P):
    cu = P["scost"]   # cost of one stockout unit
    co = P["wcost"]   # cost of one wasted unit
    return round(cu / (cu + co), 3)


# =============================================================
#  SECTION 5 — MONTE CARLO SIMULATION
#
#  We run the simulation 300 times, each with a different
#  random seed, so every run gives different numbers.
#  Then we collect:
#    - Total profit from each run
#    - Service level from each run
#    - Waste rate from each run
#  This shows us the RANGE of possible outcomes — best case,
#  worst case, and most likely (average).
# =============================================================

def monte_carlo(P, n_runs=300):
    global _seed
    profits, services, wastes = [], [], []

    for r in range(n_runs):
        _seed = r * 7919 + 1   # different seed → different random numbers

        stock = P["ss"]
        age   = 0
        t_profit = 0.0
        t_sold   = 0
        t_demand = 0
        t_spoiled= 0
        t_received = P["ss"]   # start with safety stock

        for day in range(1, P["days"] + 1):
            stock, age, res = simulate_one_day(
                stock, age, day, P, drought=False)
            t_profit  += res["profit"]
            t_sold    += res["sold"]
            t_demand  += res["demand"]
            t_spoiled += res["spoiled"]
            t_received+= res["harvest"]

        profits.append(t_profit)
        services.append(service_level(t_sold, t_demand))
        wastes.append(waste_rate(t_spoiled, t_received))

    # Simple statistics (no libraries)
    def avg(lst): return sum(lst) / len(lst)
    def sd(lst):
        m = avg(lst)
        return _sqrt(sum((x - m)**2 for x in lst) / len(lst))

    return {
        "profits":  profits,
        "services": services,
        "wastes":   wastes,
        "p_avg":    round(avg(profits),  2),
        "p_std":    round(sd(profits),   2),
        "p_best":   round(max(profits),  2),
        "p_worst":  round(min(profits),  2),
        "svc_avg":  round(avg(services), 1),
        "wst_avg":  round(avg(wastes),   1),
    }


# =============================================================
#  SECTION 6 — WHAT-IF COMPARISON
#
#  Run the simulation TWICE — once WITHOUT drought, once WITH.
#  Then show the difference in profit, service level, waste.
#  This directly answers: "How much does drought hurt us?"
# =============================================================

def what_if_comparison(P, n_runs=200):
    global _seed

    def run_set(drought_on):
        profits, services = [], []
        for r in range(n_runs):
            _seed = r * 3571 + 1
            stock = P["ss"]; age = 0
            t_profit=0.0; t_sold=0; t_demand=0
            for day in range(1, P["days"]+1):
                stock, age, res = simulate_one_day(
                    stock, age, day, P, drought=drought_on)
                t_profit += res["profit"]
                t_sold   += res["sold"]
                t_demand += res["demand"]
            profits.append(t_profit)
            services.append(service_level(t_sold, t_demand))
        avg = lambda l: sum(l)/len(l)
        return round(avg(profits),1), round(avg(services),1)

    no_drought_profit, no_drought_svc = run_set(False)
    drought_profit,    drought_svc    = run_set(True)

    profit_loss = round(no_drought_profit - drought_profit, 2)
    svc_drop    = round(no_drought_svc - drought_svc, 1)

    return {
        "no_drought_profit": no_drought_profit,
        "drought_profit":    drought_profit,
        "profit_loss":       profit_loss,
        "no_drought_svc":    no_drought_svc,
        "drought_svc":       drought_svc,
        "svc_drop":          svc_drop,
    }


# =============================================================
#  SECTION 7 — CHART DRAWING
#  All drawn using Tkinter Canvas — no matplotlib.
#  Just lines, rectangles, and text.
# =============================================================

def draw_chart(canvas, data, color, title,
               safety=None, droughts=None, second=None, second_color=None):
    canvas.delete("all")
    canvas.update()
    W = canvas.winfo_width()  or 500
    H = canvas.winfo_height() or 200
    L, R, T, B = 55, 15, 28, 28

    canvas.create_rectangle(0, 0, W, H, fill="white", outline="")
    canvas.create_text(W//2, 14, text=title,
                       fill="#1e293b", font=("Segoe UI", 9, "bold"))

    if not data:
        canvas.create_text(W//2, H//2, text="Press  ▶ RUN  to start",
                           fill="#aaaaaa", font=("Segoe UI", 10))
        return

    # Y range — combine main data and optional second series
    all_vals = list(data) + (list(second) if second else [])
    lo = min(all_vals); hi = max(all_vals)
    if lo == hi: lo -= 1; hi += 1
    lo -= (hi-lo)*0.1; hi += (hi-lo)*0.1
    n = len(data)

    def px(i): return L + (i / max(n-1, 1)) * (W - L - R)
    def py(v): return T + (1 - (v-lo)/(hi-lo)) * (H - T - B)

    # Drought shading (light pink background)
    if droughts:
        for i, d in enumerate(droughts):
            if d:
                canvas.create_rectangle(
                    px(i), T, px(min(i+1, n-1)), H-B,
                    fill="#ffe4e6", outline="")

    # Grid lines
    for s in range(5):
        gv = lo + s * (hi-lo) / 4
        gy = py(gv)
        canvas.create_line(L, gy, W-R, gy, fill="#e2e8f0", dash=(4,4))
        canvas.create_text(L-4, gy, text=f"{int(gv)}",
                           fill="#94a3b8", font=("Segoe UI",7), anchor="e")

    # Safety stock dashed line
    if safety and lo < safety < hi:
        sy = py(safety)
        canvas.create_line(L, sy, W-R, sy,
                           fill="#f59e0b", dash=(6,4), width=2)
        canvas.create_text(W-R-4, sy-8, text=f"Safety={int(safety)}",
                           fill="#f59e0b", font=("Segoe UI",7), anchor="e")

    # Axes
    canvas.create_line(L, T, L, H-B, fill="#cbd5e1")
    canvas.create_line(L, H-B, W-R, H-B, fill="#cbd5e1")

    # X-axis day numbers
    for i in range(0, n, max(1, n//8)):
        canvas.create_text(px(i), H-B+11, text=str(i+1),
                           fill="#94a3b8", font=("Segoe UI",7))

    # Main data line
    pts = []
    for i, v in enumerate(data): pts += [px(i), py(v)]
    if len(pts) >= 4:
        canvas.create_line(pts, fill=color, width=2, smooth=True)
    if pts:
        canvas.create_oval(pts[-2]-5, pts[-1]-5,
                           pts[-2]+5, pts[-1]+5,
                           fill=color, outline="white", width=2)

    # Optional second line (e.g. demand on harvest chart)
    if second and second_color:
        pts2 = []
        for i, v in enumerate(second): pts2 += [px(i), py(v)]
        if len(pts2) >= 4:
            canvas.create_line(pts2, fill=second_color,
                               width=2, dash=(5,3), smooth=True)


def draw_histogram(canvas, data, color, title):
    canvas.delete("all")
    canvas.update()
    W = canvas.winfo_width()  or 460
    H = canvas.winfo_height() or 180
    L, R, T, B = 52, 12, 28, 28
    BINS = 18

    canvas.create_rectangle(0, 0, W, H, fill="white", outline="")
    canvas.create_text(W//2, 14, text=title,
                       fill="#1e293b", font=("Segoe UI", 9, "bold"))
    if not data: return

    lo, hi = min(data), max(data)
    if lo == hi: lo -= 1; hi += 1

    counts = [0] * BINS
    for v in data:
        i = int((v-lo)/(hi-lo)*BINS)
        counts[min(i, BINS-1)] += 1
    mc = max(counts) or 1

    bx = lambda i: L + i * (W-L-R) / BINS
    by = lambda c: T + (1 - c/mc) * (H - T - B)

    for i, c in enumerate(counts):
        canvas.create_rectangle(bx(i)+1, by(c), bx(i+1)-1, H-B,
                                fill=color, outline="white")

    # Mean line
    mean_v = sum(data) / len(data)
    mx = L + (mean_v-lo)/(hi-lo) * (W-L-R)
    canvas.create_line(mx, T, mx, H-B, fill="#f59e0b", dash=(5,3), width=2)
    canvas.create_text(mx+5, T+8, text=f"avg={mean_v:.1f}",
                       fill="#c07000", font=("Segoe UI",8), anchor="w")

    canvas.create_line(L, T, L, H-B, fill="#cbd5e1")
    canvas.create_line(L, H-B, W-R, H-B, fill="#cbd5e1")
    canvas.create_text(L,   H-8, text=f"{lo:.0f}",
                       fill="#94a3b8", font=("Segoe UI",7), anchor="w")
    canvas.create_text(W-R, H-8, text=f"{hi:.0f}",
                       fill="#94a3b8", font=("Segoe UI",7), anchor="e")


# =============================================================
#  SECTION 8 — GUI (the window)
# =============================================================

root = tk.Tk()
root.title("Fresh Produce Hub — Stochastic Inventory Simulator")
root.geometry("1200x750")
root.configure(bg="#f1f5f9")

# -- Simulation variables (plain global variables, easy to follow)
stock = 0;  age = 0;  day_num = 0
running   = False
drought   = False
after_id  = None
P         = {}        # current product parameters

# Running totals
t_profit   = 0.0
t_sold     = 0
t_demand   = 0
t_spoiled  = 0
t_received = 0

# History lists for charts
h_stock   = []
h_harvest = []
h_demand  = []
h_profit  = []
h_drought = []   # True/False per day

# KPI display variables
v_day     = tk.StringVar(value="0")
v_stock   = tk.StringVar(value="—")
v_sold    = tk.StringVar(value="—")
v_spoiled = tk.StringVar(value="0")
v_stk     = tk.StringVar(value="0")
v_profit  = tk.StringVar(value="—")
v_total   = tk.StringVar(value="—")
v_svc     = tk.StringVar(value="—")
v_waste   = tk.StringVar(value="—")
v_cr      = tk.StringVar(value="—")
v_status  = tk.StringVar(value="Select a product and press  ▶ RUN")
v_weather = tk.StringVar(value="☀  Normal Weather")


# =============================================================
#  SIMULATION CONTROL FUNCTIONS
# =============================================================

def do_run():
    global stock, age, day_num, running, after_id, P
    global t_profit, t_sold, t_demand, t_spoiled, t_received
    global h_stock, h_harvest, h_demand, h_profit, h_drought

    if running: return
    P = get_params()
    if P is None: return

    if day_num == 0:   # fresh start
        stock      = P["ss"]
        age        = 0
        t_profit   = 0.0
        t_sold     = 0
        t_demand   = 0
        t_spoiled  = 0
        t_received = P["ss"]
        h_stock    = []
        h_harvest  = []
        h_demand   = []
        h_profit   = []
        h_drought  = []
        # Show Critical Ratio before starting
        cr = critical_ratio(P)
        v_cr.set(f"{cr}  (Cu={P['scost']} / Co={P['wcost']})")

    running = True
    v_status.set("🌱  Simulation running…")
    do_tick()


def do_pause():
    global running, after_id
    running = False
    if after_id: root.after_cancel(after_id)
    v_status.set("⏸  Paused. Press RUN to continue.")


def do_reset():
    global stock,age,day_num,running,drought,after_id
    global t_profit,t_sold,t_demand,t_spoiled,t_received
    global h_stock,h_harvest,h_demand,h_profit,h_drought

    do_pause()
    stock=age=day_num=0; drought=False
    t_profit=t_sold=t_demand=t_spoiled=t_received=0
    h_stock=h_harvest=h_demand=h_profit=h_drought=[]

    for var, val in [
        (v_day,"0"),(v_stock,"—"),(v_sold,"—"),(v_spoiled,"0"),
        (v_stk,"0"),(v_profit,"—"),(v_total,"—"),
        (v_svc,"—"),(v_waste,"—"),(v_cr,"—")
    ]:
        var.set(val)

    v_weather.set("☀  Normal Weather")
    v_status.set("Reset. Press  ▶ RUN  to start.")
    d_btn.config(text="🌵  Trigger Drought", bg="#fff1f2", fg="#dc2626")

    for c in [c_stock, c_harvest, c_profit]:
        c.delete("all")
        c.update()
        W = c.winfo_width() or 400
        H = c.winfo_height() or 180
        c.create_rectangle(0,0,W,H, fill="white", outline="")
        c.create_text(W//2,H//2, text="Press  ▶ RUN  to start",
                      fill="#aaaaaa", font=("Segoe UI",10))


def do_toggle_drought():
    global drought
    if day_num == 0:
        v_status.set("⚠  Start the simulation first!")
        return
    drought = not drought
    if drought:
        d_btn.config(text="✅  End Drought", bg="#f0fdf4", fg="#16a34a")
        v_weather.set("🌵  DROUGHT ACTIVE")
        pct = int(P.get("dfact", 0.3) * 100)
        v_status.set(
            f"🌵  DROUGHT on!\n"
            f"Harvest = {pct}% of normal.\n"
            f"Safety stock auto-raised by 80%.")
    else:
        d_btn.config(text="🌵  Trigger Drought", bg="#fff1f2", fg="#dc2626")
        v_weather.set("☀  Normal Weather")
        v_status.set("✅  Drought over. Normal harvest resumed.")


def do_tick():
    """Runs ONE day of simulation, then schedules itself again."""
    global stock, age, day_num, running, after_id
    global t_profit, t_sold, t_demand, t_spoiled, t_received

    if not running: return

    if day_num >= P["days"]:
        running = False
        svc = service_level(t_sold, t_demand)
        wst = waste_rate(t_spoiled, t_received)
        v_status.set(
            f"✅  Done!  {day_num} days simulated.\n"
            f"Total Profit: ₹{t_profit:,.0f}  |  "
            f"Service: {svc}%  |  Waste: {wst}%")
        show_summary()
        return

    day_num += 1
    stock, age, res = simulate_one_day(stock, age, day_num, P, drought)

    # Accumulate totals
    t_profit   += res["profit"]
    t_sold     += res["sold"]
    t_demand   += res["demand"]
    t_spoiled  += res["spoiled"]
    t_received += res["harvest"]

    # Save to history
    h_stock.append(res["stock"])
    h_harvest.append(res["harvest"])
    h_demand.append(res["demand"])
    h_profit.append(t_profit)
    h_drought.append(drought)

    # Update KPI cards
    svc = service_level(t_sold, t_demand)
    wst = waste_rate(t_spoiled, t_received)
    sign = "+" if res["profit"] >= 0 else ""
    tsign = "+" if t_profit >= 0 else ""

    v_day.set(str(day_num))
    v_stock.set(str(res["stock"]))
    v_sold.set(str(res["sold"]))
    v_spoiled.set(str(res["spoiled"]))
    v_stk.set(str(res["stockout"]))
    v_profit.set(f"{sign}₹{res['profit']:,.0f}")
    v_total.set(f"{tsign}₹{t_profit:,.0f}")
    v_svc.set(f"{svc}%")
    v_waste.set(f"{wst}%")

    # Redraw charts
    draw_chart(c_stock,   h_stock,
               "#0891b2", "📦  Stock Level",
               safety=P["ss"], droughts=h_drought)

    draw_chart(c_harvest, h_harvest,
               "#16a34a", "🌾  Harvest  (solid)  vs  Demand  (dashed)",
               droughts=h_drought,
               second=h_demand, second_color="#f59e0b")

    draw_chart(c_profit,  h_profit,
               "#7c3aed", "💰  Cumulative Profit  (₹)")

    after_id = root.after(spd.get(), do_tick)


def show_summary():
    """Pop-up showing all KPIs after simulation ends."""
    svc = service_level(t_sold, t_demand)
    wst = waste_rate(t_spoiled, t_received)
    cr  = critical_ratio(P)

    win = tk.Toplevel(root)
    win.title("Simulation Summary")
    win.configure(bg="#f8fafc")
    win.geometry("420x400")
    win.resizable(False, False)

    tk.Label(win, text="📋  Simulation Summary",
             bg="#f8fafc", fg="#1e293b",
             font=("Segoe UI", 13, "bold")).pack(pady=(14,4))
    tk.Label(win, text=f"{day_num} days  |  {product_var.get().split('(')[0].strip()}",
             bg="#f8fafc", fg="#64748b",
             font=("Segoe UI",9)).pack()

    sf = tk.Frame(win, bg="#f8fafc")
    sf.pack(fill="x", padx=16, pady=10)

    rows = [
        ("Total Profit",    f"₹{t_profit:,.0f}",    "#7c3aed"),
        ("Service Level",   f"{svc}%",               "#16a34a"),
        ("Waste Rate",      f"{wst}%",               "#dc2626"),
        ("Total Sold",      f"{t_sold} units",       "#0891b2"),
        ("Total Spoiled",   f"{t_spoiled} units",    "#dc2626"),
        ("Total Stockouts", f"{t_demand-t_sold} units","#d97706"),
        ("Critical Ratio",  f"CR = {cr}",            "#2563eb"),
        ("CR Means",
         f"Cu={P['scost']} > Co={P['wcost']} → Keep more stock"
         if P["scost"] > P["wcost"] else
         f"Co={P['wcost']} > Cu={P['scost']} → Reduce stock",
         "#64748b"),
    ]

    for i, (lbl, val, col) in enumerate(rows):
        r = i // 2; c = i % 2
        sf.columnconfigure(c, weight=1)
        f = tk.Frame(sf, bg="white",
                     highlightthickness=1,
                     highlightbackground="#e2e8f0")
        f.grid(row=r, column=c, sticky="ew", padx=3, pady=3)
        tk.Label(f, text=lbl, bg="white", fg="#64748b",
                 font=("Segoe UI",8)).pack(anchor="w", padx=8, pady=(5,0))
        tk.Label(f, text=val, bg="white", fg=col,
                 font=("Segoe UI",11,"bold"),
                 wraplength=170).pack(anchor="w", padx=8, pady=(0,5))

    tk.Button(win, text="Close", bg="#2563eb", fg="white",
              font=("Segoe UI",9,"bold"), relief="flat",
              padx=20, pady=6,
              command=win.destroy).pack(pady=(0,14))


def do_monte_carlo():
    """Run 300 simulations. Show profit, service, waste distributions."""
    params = get_params()
    if params is None: return

    v_status.set("🎲  Running 300 simulations…")
    root.update_idletasks()

    res = monte_carlo(params, n_runs=300)
    cr  = critical_ratio(params)

    win = tk.Toplevel(root)
    win.title("Monte Carlo — 300 Simulations")
    win.configure(bg="#f8fafc")
    win.geometry("600x560")

    tk.Label(win, text="🎲  Monte Carlo Analysis",
             bg="#f8fafc", fg="#1e293b",
             font=("Segoe UI",13,"bold")).pack(pady=(12,2))
    tk.Label(win,
             text=f"300 independent runs  ×  {params['days']} days  |  "
                  f"Critical Ratio = {cr}",
             bg="#f8fafc", fg="#64748b",
             font=("Segoe UI",9)).pack()

    # Stats grid
    sf = tk.Frame(win, bg="#f8fafc")
    sf.pack(fill="x", padx=16, pady=8)
    stats = [
        ("Avg Total Profit",   f"₹{res['p_avg']:,.0f}",   "#2563eb"),
        ("Std Deviation",      f"₹{res['p_std']:,.0f}",   "#d97706"),
        ("Best Run",           f"₹{res['p_best']:,.0f}",  "#16a34a"),
        ("Worst Run",          f"₹{res['p_worst']:,.0f}", "#dc2626"),
        ("Avg Service Level",  f"{res['svc_avg']}%",      "#0891b2"),
        ("Avg Waste Rate",     f"{res['wst_avg']}%",      "#dc2626"),
    ]
    for i, (lbl, val, col) in enumerate(stats):
        r = i // 2; c = i % 2
        sf.columnconfigure(c, weight=1)
        f = tk.Frame(sf, bg="white",
                     highlightthickness=1, highlightbackground="#e2e8f0")
        f.grid(row=r, column=c, sticky="ew", padx=3, pady=2)
        tk.Label(f, text=lbl, bg="white", fg="#64748b",
                 font=("Segoe UI",8)).pack(anchor="w", padx=8, pady=(5,0))
        tk.Label(f, text=val, bg="white", fg=col,
                 font=("Segoe UI",13,"bold")).pack(anchor="w", padx=8, pady=(0,5))

    # Three histograms: profit, service, waste
    hf = tk.Frame(win, bg="#f8fafc")
    hf.pack(fill="both", expand=True, padx=16, pady=(0,12))
    hf.columnconfigure(0, weight=2)
    hf.columnconfigure(1, weight=1)
    hf.columnconfigure(2, weight=1)
    hf.rowconfigure(0, weight=1)

    for col, (data, color, title) in enumerate([
        (res["profits"],  "#3b82f6", "Profit Distribution (₹)"),
        (res["services"], "#16a34a", "Service Level (%)"),
        (res["wastes"],   "#dc2626", "Waste Rate (%)"),
    ]):
        frame = tk.Frame(hf, bg="white",
                         highlightthickness=1,
                         highlightbackground="#e2e8f0")
        frame.grid(row=0, column=col, sticky="nsew",
                   padx=(0,4) if col < 2 else 0)
        frame.rowconfigure(0,weight=1); frame.columnconfigure(0,weight=1)
        cv = tk.Canvas(frame, bg="white", highlightthickness=0)
        cv.grid(sticky="nsew", padx=4, pady=4)
        win.update_idletasks()
        draw_histogram(cv, data, color, title)

    v_status.set(
        f"✅  MC done — avg profit ₹{res['p_avg']:,.0f}  |  "
        f"service {res['svc_avg']}%  |  waste {res['wst_avg']}%")


def do_what_if():
    """Compare Normal vs Drought — side by side."""
    params = get_params()
    if params is None: return

    v_status.set("🔬  Running What-If comparison…")
    root.update_idletasks()

    wi = what_if_comparison(params, n_runs=200)

    win = tk.Toplevel(root)
    win.title("What-If: Normal vs Drought")
    win.configure(bg="#f8fafc")
    win.geometry("420x340")
    win.resizable(False, False)

    tk.Label(win, text="🔬  What-If: Normal vs Drought",
             bg="#f8fafc", fg="#1e293b",
             font=("Segoe UI",13,"bold")).pack(pady=(14,4))
    tk.Label(win, text="200 Monte Carlo runs each  (same parameters)",
             bg="#f8fafc", fg="#64748b",
             font=("Segoe UI",9)).pack()

    sf = tk.Frame(win, bg="#f8fafc")
    sf.pack(fill="x", padx=16, pady=12)
    sf.columnconfigure(0,weight=1); sf.columnconfigure(1,weight=1); sf.columnconfigure(2,weight=1)

    headers = ["", "☀  Normal", "🌵  Drought"]
    colors  = ["#1e293b", "#16a34a", "#dc2626"]
    for c, (h, col) in enumerate(zip(headers, colors)):
        tk.Label(sf, text=h, bg="#f8fafc", fg=col,
                 font=("Segoe UI",10,"bold")).grid(
                     row=0, column=c, pady=(0,6))

    rows = [
        ("Avg Total Profit",
         f"₹{wi['no_drought_profit']:,.0f}",
         f"₹{wi['drought_profit']:,.0f}"),
        ("Avg Service Level",
         f"{wi['no_drought_svc']}%",
         f"{wi['drought_svc']}%"),
    ]
    for r, (lbl, nval, dval) in enumerate(rows, start=1):
        tk.Label(sf, text=lbl, bg="#f8fafc", fg="#64748b",
                 font=("Segoe UI",9)).grid(row=r, column=0, sticky="w", pady=4)
        tk.Label(sf, text=nval, bg="#f8fafc", fg="#16a34a",
                 font=("Segoe UI",12,"bold")).grid(row=r, column=1)
        tk.Label(sf, text=dval, bg="#f8fafc", fg="#dc2626",
                 font=("Segoe UI",12,"bold")).grid(row=r, column=2)

    # Impact summary
    impact = tk.Frame(win, bg="#fef3c7",
                      highlightthickness=1,
                      highlightbackground="#f59e0b")
    impact.pack(fill="x", padx=16, pady=(0,8))
    tk.Label(impact,
             text=f"💸  Drought reduces profit by  ₹{wi['profit_loss']:,.0f}\n"
                  f"📉  Service level drops by  {wi['svc_drop']}%",
             bg="#fef3c7", fg="#92400e",
             font=("Segoe UI",10,"bold"),
             justify="center").pack(pady=10)

    tk.Label(win,
             text=f"Drought factor = {int(params['dfact']*100)}% of normal harvest.\n"
                  f"Safety stock auto-raises 80% during drought as defence.",
             bg="#f8fafc", fg="#64748b",
             font=("Segoe UI",8),
             justify="center").pack()

    tk.Button(win, text="Close", bg="#2563eb", fg="white",
              font=("Segoe UI",9,"bold"), relief="flat",
              padx=20, pady=6,
              command=win.destroy).pack(pady=10)

    v_status.set(
        f"✅  What-If done — "
        f"Drought costs ₹{wi['profit_loss']:,.0f} in profit")


# =============================================================
#  SECTION 9 — READ PARAMETERS FROM ENTRY BOXES
# =============================================================

def get_params():
    name = product_var.get()
    if not name:
        messagebox.showwarning("No Product", "Please select a product first.")
        return None
    P = dict(PRODUCTS[name])   # copy preset
    try:
        P["shelf"] = int(e_shelf.get())
        P["sup"]   = float(e_sup.get())
        P["std"]   = float(e_std.get())
        P["dmin"]  = int(e_dmin.get())
        P["dmax"]  = int(e_dmax.get())
        P["ss"]    = int(e_ss.get())
        P["oq"]    = int(e_oq.get())
        P["price"] = float(e_price.get())
        P["wcost"] = float(e_wcost.get())
        P["scost"] = float(e_scost.get())
        P["hcost"] = float(e_hcost.get())
        P["days"]  = int(e_days.get())
    except ValueError as e:
        messagebox.showerror("Bad Input", f"Check your values.\n{e}")
        return None
    return P

def load_preset(event=None):
    name = product_var.get()
    if not name: return
    P = PRODUCTS[name]
    for entry, key in [
        (e_shelf,"shelf"), (e_sup,"sup"),   (e_std,"std"),
        (e_dmin,"dmin"),   (e_dmax,"dmax"), (e_ss,"ss"),
        (e_oq,"oq"),       (e_price,"price"),(e_wcost,"wcost"),
        (e_scost,"scost"), (e_hcost,"hcost"),(e_days,"days"),
    ]:
        entry.delete(0, "end")
        entry.insert(0, str(P[key]))
    do_reset()


# =============================================================
#  SECTION 10 — BUILD THE WINDOW
# =============================================================

# -- Header ---------------------------------------------------
hdr = tk.Frame(root, bg="#1e3a5f", height=50)
hdr.pack(fill="x")
hdr.pack_propagate(False)
tk.Label(hdr, text="🌿  Fresh Produce Hub",
         bg="#1e3a5f", fg="white",
         font=("Segoe UI",14,"bold")).pack(side="left", padx=14)
tk.Label(hdr, text="Stochastic Perishable Inventory Simulator",
         bg="#1e3a5f", fg="#94a3b8",
         font=("Segoe UI",10)).pack(side="left")
tk.Label(hdr, textvariable=v_weather,
         bg="#1e3a5f", fg="#4ade80",
         font=("Segoe UI",11,"bold")).pack(side="right", padx=14)

# -- Body -----------------------------------------------------
body = tk.Frame(root, bg="#f1f5f9")
body.pack(fill="both", expand=True, padx=10, pady=8)
body.columnconfigure(1, weight=1)
body.rowconfigure(0, weight=1)

# -- Sidebar --------------------------------------------------
sb = tk.Frame(body, bg="white", width=255,
              highlightthickness=1, highlightbackground="#e2e8f0")
sb.grid(row=0, column=0, sticky="nsew", padx=(0,8))
sb.pack_propagate(False)

def sec(txt):
    f = tk.Frame(sb, bg="white")
    f.pack(fill="x", padx=12, pady=(10,3))
    tk.Label(f, text=txt, bg="white", fg="#1e293b",
             font=("Segoe UI",8,"bold")).pack(side="left")
    tk.Frame(f, bg="#e2e8f0", height=1).pack(
        side="left", fill="x", expand=True, padx=6)

def erow(lbl, default):
    f = tk.Frame(sb, bg="white")
    f.pack(fill="x", padx=12, pady=1)
    tk.Label(f, text=lbl, bg="white", fg="#64748b",
             font=("Segoe UI",8), width=22, anchor="w").pack(side="left")
    e = tk.Entry(f, bg="#f8fafc", fg="#1e293b",
                 font=("Segoe UI",8), width=7,
                 relief="solid", bd=1)
    e.insert(0, str(default))
    e.pack(side="right")
    return e

def sbtn(txt, bg, cmd):
    tk.Button(sb, text=txt, bg=bg, fg="white",
              font=("Segoe UI",9,"bold"), relief="flat",
              cursor="hand2", pady=7,
              command=cmd).pack(fill="x", padx=12, pady=2)

# Product
sec("PRODUCT")
product_var = tk.StringVar()
cb = ttk.Combobox(sb, textvariable=product_var,
                  values=list(PRODUCTS.keys()),
                  state="readonly", font=("Segoe UI",8), width=27)
cb.pack(padx=12, pady=(0,6), fill="x")
cb.bind("<<ComboboxSelected>>", load_preset)

# Parameters
sec("PARAMETERS")
e_shelf = erow("Shelf Life (days)", 7)
e_sup   = erow("Avg Harvest / day", 120)
e_std   = erow("Harvest Variation", 18)
e_dmin  = erow("Min Demand / day", 80)
e_dmax  = erow("Max Demand / day", 130)
e_ss    = erow("Safety Stock", 70)
e_oq    = erow("Reorder Quantity", 100)
e_price = erow("Sale Price (₹)", 3.5)
e_wcost = erow("Waste Cost / unit (₹)", 1.2)
e_scost = erow("Stockout Cost / unit (₹)", 2.5)
e_hcost = erow("Holding Cost / unit (₹)", 0.05)
e_days  = erow("Days to Simulate", 60)

# Critical Ratio display
sec("CRITICAL RATIO  =  Cu / (Cu + Co)")
tk.Label(sb, textvariable=v_cr, bg="white", fg="#2563eb",
         font=("Segoe UI",8), wraplength=220,
         justify="left").pack(padx=12, anchor="w")

# Speed
sec("SPEED  (ms per day)")
spd = tk.IntVar(value=120)
tk.Scale(sb, variable=spd, from_=20, to=600,
         orient="horizontal", bg="white",
         troughcolor="#e2e8f0", highlightthickness=0,
         showvalue=True, length=215).pack(padx=12)

# Control buttons
sec("CONTROLS")
sbtn("▶   RUN",              "#2563eb", do_run)
sbtn("⏸   PAUSE",            "#d97706", do_pause)
sbtn("↺   RESET",            "#64748b", do_reset)

d_btn = tk.Button(sb, text="🌵  Trigger Drought",
                  bg="#fff1f2", fg="#dc2626",
                  font=("Segoe UI",9,"bold"),
                  relief="solid", bd=1,
                  cursor="hand2", pady=7,
                  command=do_toggle_drought)
d_btn.pack(fill="x", padx=12, pady=2)

sbtn("🎲   Monte Carlo (300 runs)", "#0891b2", do_monte_carlo)
sbtn("🔬   What-If: Normal vs Drought", "#7c3aed", do_what_if)

# Status label
tk.Label(sb, textvariable=v_status,
         bg="#eff6ff", fg="#1d4ed8",
         font=("Segoe UI",8), wraplength=225,
         justify="left", padx=8, pady=6).pack(
             fill="x", side="bottom", padx=8, pady=8)

# -- Right side -----------------------------------------------
right = tk.Frame(body, bg="#f1f5f9")
right.grid(row=0, column=1, sticky="nsew")
right.rowconfigure(1, weight=2)
right.rowconfigure(2, weight=1)
right.columnconfigure(0, weight=1)

# KPI cards (2 rows of 5)
kf = tk.Frame(right, bg="#f1f5f9")
kf.grid(row=0, column=0, sticky="ew", pady=(0,6))

kpi_defs = [
    ("Day",          v_day,     "#1e293b"),
    ("Stock",        v_stock,   "#0891b2"),
    ("Sold",         v_sold,    "#16a34a"),
    ("Spoiled",      v_spoiled, "#dc2626"),
    ("Stockout",     v_stk,     "#d97706"),
    ("Today ₹",      v_profit,  "#2563eb"),
    ("Total ₹",      v_total,   "#7c3aed"),
    ("Service %",    v_svc,     "#16a34a"),
    ("Waste %",      v_waste,   "#dc2626"),
    ("CR",           v_cr,      "#2563eb"),
]
for i, (lbl, var, col) in enumerate(kpi_defs):
    r = i // 5
    c = i % 5
    kf.columnconfigure(c, weight=1)
    card = tk.Frame(kf, bg="white",
                    highlightthickness=1,
                    highlightbackground="#e2e8f0")
    card.grid(row=r, column=c, sticky="ew", padx=2, pady=2)
    tk.Label(card, text=lbl.upper(), bg="white", fg="#94a3b8",
             font=("Segoe UI",7,"bold")).pack(pady=(5,0))
    tk.Label(card, textvariable=var, bg="white", fg=col,
             font=("Segoe UI",13,"bold"),
             wraplength=110).pack(pady=(0,5))

# Charts
def make_chart(parent, row, col=0, padx=0, pady=0):
    f = tk.Frame(parent, bg="white",
                 highlightthickness=1,
                 highlightbackground="#e2e8f0")
    f.grid(row=row, column=col, sticky="nsew",
           padx=padx, pady=pady)
    f.rowconfigure(0, weight=1)
    f.columnconfigure(0, weight=1)
    c = tk.Canvas(f, bg="white", highlightthickness=0)
    c.grid(sticky="nsew", padx=6, pady=6)
    return c

c_stock = make_chart(right, row=1, pady=(0,4))

bot = tk.Frame(right, bg="#f1f5f9")
bot.grid(row=2, column=0, sticky="nsew")
bot.columnconfigure(0, weight=1)
bot.columnconfigure(1, weight=1)
bot.rowconfigure(0, weight=1)

c_harvest = make_chart(bot, row=0, col=0, padx=(0,4))
c_profit  = make_chart(bot, row=0, col=1)

# -- Style dropdown -------------------------------------------
style = ttk.Style(root)
style.theme_use("clam")
style.configure("TCombobox",
                fieldbackground="white", background="white",
                foreground="#1e293b", selectbackground="#2563eb",
                selectforeground="white", arrowcolor="#64748b")
style.map("TCombobox", fieldbackground=[("readonly","white")])

# -- Load first preset and start ------------------------------
product_var.set(list(PRODUCTS.keys())[0])
load_preset()

root.mainloop()