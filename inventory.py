"""
Agricultural Inventory Management System
Clean, user-friendly Tkinter UI with:
  - Dashboard with live KPI cards
  - Stock Tracker with freshness bars
  - Orders & Supply panel
  - Alerts panel
  - Analysis charts
  - Settings
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import math

# ─────────────────────────────────────────────
#  OWN RANDOM (no import random)
# ─────────────────────────────────────────────
_seed = int(time.time() * 1000) % (2 ** 32)

def _rand():
    global _seed
    _seed = (1664525 * _seed + 1013904223) % (2 ** 32)
    return _seed / (2 ** 32)

def rand_int(lo, hi):
    return lo + int(_rand() * (hi - lo + 1))

def _sqrt(x):
    if x <= 0: return 0.0
    g = x / 2.0
    for _ in range(40): g = (g + x / g) / 2.0
    return g

# ─────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────
C = {
    "bg":        "#F8FAF5",   # page background
    "sidebar":   "#1C3A2A",   # dark green sidebar
    "sidebar_h": "#2A5240",   # sidebar hover
    "primary":   "#2D6A4F",   # primary green
    "accent":    "#40916C",   # accent green
    "card":      "#FFFFFF",
    "border":    "#E0E8E2",
    "text":      "#1A2E22",
    "muted":     "#6B8F71",
    "danger":    "#C0392B",
    "warning":   "#D4890A",
    "success":   "#27AE60",
    "info":      "#2471A3",
    "purple":    "#7D3C98",
    "teal":      "#148F77",
    "red_bg":    "#FDEDEC",
    "amb_bg":    "#FEF9E7",
    "grn_bg":    "#EAFAF1",
    "blu_bg":    "#EBF5FB",
    "pur_bg":    "#F5EEF8",
}

FONTS = {
    "h1":    ("Segoe UI", 20, "bold"),
    "h2":    ("Segoe UI", 14, "bold"),
    "h3":    ("Segoe UI", 11, "bold"),
    "body":  ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "mono":  ("Consolas", 9),
    "kpi":   ("Segoe UI", 22, "bold"),
}

# ─────────────────────────────────────────────
#  SAMPLE DATA
# ─────────────────────────────────────────────
PRODUCTS = [
    {"name": "Tomatoes",     "category": "Vegetable", "qty": 85,  "unit": "kg",  "shelf": 5,  "age": 2, "safety": 30, "reorder": 60,  "price": 35,  "location": "Cold Room A", "supplier": "Farm Patel"},
    {"name": "Strawberries", "category": "Fruit",     "qty": 22,  "unit": "kg",  "shelf": 3,  "age": 1, "safety": 15, "reorder": 40,  "price": 120, "location": "Cold Room B", "supplier": "Berry Farm"},
    {"name": "Spinach",      "category": "Vegetable", "qty": 12,  "unit": "kg",  "shelf": 4,  "age": 3, "safety": 20, "reorder": 35,  "price": 45,  "location": "Cold Room A", "supplier": "Green Fields"},
    {"name": "Milk",         "category": "Dairy",     "qty": 140, "unit": "L",   "shelf": 7,  "age": 1, "safety": 50, "reorder": 100, "price": 52,  "location": "Cold Room C", "supplier": "Dairy Co"},
    {"name": "Bread",        "category": "Bakery",    "qty": 38,  "unit": "pcs", "shelf": 2,  "age": 1, "safety": 20, "reorder": 50,  "price": 30,  "location": "Shelf 1",     "supplier": "City Bakery"},
    {"name": "Potatoes",     "category": "Vegetable", "qty": 200, "unit": "kg",  "shelf": 14, "age": 4, "safety": 60, "reorder": 120, "price": 22,  "location": "Dry Store",   "supplier": "Farm Patel"},
    {"name": "Mangoes",      "category": "Fruit",     "qty": 55,  "unit": "kg",  "shelf": 6,  "age": 2, "safety": 25, "reorder": 70,  "price": 90,  "location": "Cold Room B", "supplier": "Mango Estate"},
    {"name": "Wheat Flour",  "category": "Grain",     "qty": 300, "unit": "kg",  "shelf": 60, "age": 10,"safety": 80, "reorder": 200, "price": 28,  "location": "Dry Store",   "supplier": "Mill Corp"},
]

ALERTS = [
    {"type": "critical", "msg": "Spinach expires in 1 day — only 12 kg left",        "time": "08:15"},
    {"type": "critical", "msg": "Bread stock at 38 pcs — below safety stock (20)",    "time": "08:02"},
    {"type": "warning",  "msg": "Strawberries expiring in 2 days — consider discount","time": "07:55"},
    {"type": "warning",  "msg": "Tomato supply delayed — Farm Patel ETA shifted +1d", "time": "07:30"},
    {"type": "info",     "msg": "Milk delivery received: 60 L from Dairy Co",         "time": "06:50"},
    {"type": "info",     "msg": "Reorder triggered: Spinach — 35 kg ordered",         "time": "06:45"},
    {"type": "suggest",  "msg": "Apply 20% discount on Spinach to clear before expiry","time": "06:40"},
    {"type": "suggest",  "msg": "Increase Strawberry safety stock — peak season ahead","time": "Yesterday"},
]

ORDERS_IN = [
    {"supplier": "Farm Patel",   "product": "Tomatoes",  "qty": "60 kg",  "eta": "Today 2pm",   "status": "On the way"},
    {"supplier": "Green Fields", "product": "Spinach",   "qty": "35 kg",  "eta": "Today 4pm",   "status": "Confirmed"},
    {"supplier": "Berry Farm",   "product": "Strawberries","qty":"40 kg", "eta": "Tomorrow",     "status": "Confirmed"},
    {"supplier": "Dairy Co",     "product": "Milk",      "qty": "100 L",  "eta": "Tomorrow 8am","status": "Scheduled"},
    {"supplier": "City Bakery",  "product": "Bread",     "qty": "50 pcs", "eta": "Tomorrow 7am","status": "Scheduled"},
]

ORDERS_OUT = [
    {"buyer": "Market A",   "product": "Tomatoes",  "qty": "40 kg",  "date": "Today",    "status": "Fulfilled"},
    {"buyer": "Hotel B",    "product": "Milk",      "qty": "20 L",   "date": "Today",    "status": "Pending"},
    {"buyer": "Canteen C",  "product": "Potatoes",  "qty": "30 kg",  "date": "Today",    "status": "Fulfilled"},
    {"buyer": "Market A",   "product": "Spinach",   "qty": "15 kg",  "date": "Today",    "status": "Shortfall"},
    {"buyer": "Store D",    "product": "Mangoes",   "qty": "20 kg",  "date": "Tomorrow", "status": "Confirmed"},
]

# ─────────────────────────────────────────────
#  HELPER WIDGETS
# ─────────────────────────────────────────────

def make_card(parent, **kwargs):
    f = tk.Frame(parent, bg=C["card"],
                 highlightthickness=1, highlightbackground=C["border"],
                 **kwargs)
    return f

def section_label(parent, text):
    tk.Label(parent, text=text.upper(), bg=parent["bg"],
             fg=C["muted"], font=("Segoe UI", 8, "bold"),
             anchor="w").pack(fill="x", padx=2, pady=(10, 3))

def divider(parent):
    tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=6)

# ─────────────────────────────────────────────
#  FRESHNESS BAR  (canvas widget)
# ─────────────────────────────────────────────

def draw_freshness(canvas, age, shelf, width=120, height=12):
    canvas.delete("all")
    canvas.config(width=width, height=height)
    remaining = max(0, shelf - age)
    ratio = remaining / shelf if shelf > 0 else 0
    if ratio > 0.5:   color = C["success"]
    elif ratio > 0.2: color = C["warning"]
    else:             color = C["danger"]
    canvas.create_rectangle(0, 0, width, height, fill="#E8F0EA", outline="")
    fill_w = int(ratio * width)
    if fill_w > 0:
        canvas.create_rectangle(0, 0, fill_w, height, fill=color, outline="")
    days_left = remaining
    label = f"{days_left}d left"
    canvas.create_text(width // 2, height // 2, text=label,
                       font=("Segoe UI", 7, "bold"),
                       fill="white" if fill_w > 50 else C["text"])

# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────

class AgriInventoryApp:

    def __init__(self, root):
        self.root = root
        self.root.title("AgriStock — Agricultural Inventory Management")
        self.root.geometry("1280x780")
        self.root.configure(bg=C["bg"])
        self.root.minsize(1000, 650)

        self.active_page = tk.StringVar(value="Dashboard")
        self._build_ui()
        self._start_clock()

    # ── TOP BAR ──────────────────────────────

    def _build_ui(self):
        # Top bar
        topbar = tk.Frame(self.root, bg=C["sidebar"], height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="🌿  AgriStock",
                 bg=C["sidebar"], fg="white",
                 font=("Segoe UI", 15, "bold")).pack(side="left", padx=18)

        tk.Label(topbar, text="Agricultural Inventory Management",
                 bg=C["sidebar"], fg="#A8C9B0",
                 font=("Segoe UI", 10)).pack(side="left")

        # Clock
        self.clock_var = tk.StringVar()
        tk.Label(topbar, textvariable=self.clock_var,
                 bg=C["sidebar"], fg="#A8C9B0",
                 font=("Segoe UI", 10)).pack(side="right", padx=18)

        # Alert badge
        alert_count = sum(1 for a in ALERTS if a["type"] == "critical")
        if alert_count:
            tk.Label(topbar, text=f"  {alert_count} critical alerts  ",
                     bg=C["danger"], fg="white",
                     font=("Segoe UI", 9, "bold"),
                     cursor="hand2").pack(side="right", padx=6, pady=10)

        # Body: sidebar + content
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self.content_frame = tk.Frame(body, bg=C["bg"])
        self.content_frame.pack(side="left", fill="both", expand=True)

        self._show_page("Dashboard")

    # ── SIDEBAR ──────────────────────────────

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=C["sidebar"], width=200)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        tk.Frame(sb, bg=C["sidebar"], height=12).pack()

        nav_items = [
            ("Dashboard",    "📊"),
            ("Stock Tracker","📦"),
            ("Orders",       "🚚"),
            ("Alerts",       "🔔"),
            ("Analysis",     "📈"),
            ("Settings",     "⚙️"),
        ]

        self.nav_btns = {}
        for label, icon in nav_items:
            btn = tk.Button(
                sb,
                text=f"  {icon}  {label}",
                bg=C["sidebar"], fg="white",
                font=("Segoe UI", 10),
                relief="flat", anchor="w",
                padx=14, pady=10,
                cursor="hand2",
                activebackground=C["sidebar_h"],
                activeforeground="white",
                command=lambda l=label: self._show_page(l)
            )
            btn.pack(fill="x")
            self.nav_btns[label] = btn

        # Bottom: weather widget
        tk.Frame(sb, bg=C["sidebar"]).pack(fill="y", expand=True)
        weather = tk.Frame(sb, bg="#142B1E", padx=12, pady=10)
        weather.pack(fill="x")
        tk.Label(weather, text="☀  Today's Weather", bg="#142B1E",
                 fg="#A8C9B0", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(weather, text="34°C  •  Clear  •  Normal harvest expected",
                 bg="#142B1E", fg="#6B9E75",
                 font=("Segoe UI", 8), wraplength=175,
                 justify="left").pack(anchor="w", pady=(3, 0))

    def _show_page(self, name):
        self.active_page.set(name)
        for label, btn in self.nav_btns.items():
            btn.config(bg=C["sidebar_h"] if label == name else C["sidebar"])

        for w in self.content_frame.winfo_children():
            w.destroy()

        pages = {
            "Dashboard":    self._page_dashboard,
            "Stock Tracker":self._page_stock,
            "Orders":       self._page_orders,
            "Alerts":       self._page_alerts,
            "Analysis":     self._page_analysis,
            "Settings":     self._page_settings,
        }
        pages.get(name, self._page_dashboard)()

    # ══════════════════════════════════════════
    #  PAGE: DASHBOARD
    # ══════════════════════════════════════════

    def _page_dashboard(self):
        cf = self.content_frame

        # Scrollable
        canvas = tk.Canvas(cf, bg=C["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(cf, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=C["bg"])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_resize(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", on_resize)
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))

        pad = {"padx": 20, "pady": 6}

        # Page title
        title_row = tk.Frame(inner, bg=C["bg"])
        title_row.pack(fill="x", padx=20, pady=(16, 4))
        tk.Label(title_row, text="Dashboard", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(side="left")
        tk.Label(title_row, text="Today, " + time.strftime("%d %b %Y"),
                 bg=C["bg"], fg=C["muted"],
                 font=FONTS["body"]).pack(side="right", pady=8)

        # ── KPI CARDS ──
        kpi_frame = tk.Frame(inner, bg=C["bg"])
        kpi_frame.pack(fill="x", padx=20, pady=(4, 8))
        kpis = [
            ("Total Stock",     "642 kg / L",  C["primary"],  "Across 8 products"),
            ("Expiring Today",  "12 kg",       C["danger"],   "Spinach — act now"),
            ("Low Stock Items", "2",           C["warning"],  "Spinach, Bread"),
            ("Inbound Today",   "2 orders",    C["info"],     "Tomatoes + Spinach"),
            ("Service Level",   "94.2%",       C["success"],  "This week"),
            ("Waste This Week", "8.4 kg",      C["purple"],   "↓ 12% vs last week"),
        ]
        for i, (lbl, val, col, sub) in enumerate(kpis):
            kpi_frame.columnconfigure(i, weight=1)
            card = make_card(kpi_frame)
            card.grid(row=0, column=i, padx=4, pady=2, sticky="ew")
            tk.Label(card, text=lbl, bg=C["card"], fg=C["muted"],
                     font=FONTS["small"]).pack(anchor="w", padx=10, pady=(8,0))
            tk.Label(card, text=val, bg=C["card"], fg=col,
                     font=FONTS["kpi"]).pack(anchor="w", padx=10)
            tk.Label(card, text=sub, bg=C["card"], fg=C["muted"],
                     font=FONTS["small"]).pack(anchor="w", padx=10, pady=(0,8))

        # ── MIDDLE ROW: stock bar chart + activity feed ──
        mid = tk.Frame(inner, bg=C["bg"])
        mid.pack(fill="x", padx=20, pady=4)
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)

        # Stock levels bar chart
        chart_card = make_card(mid)
        chart_card.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        tk.Label(chart_card, text="Stock levels by product",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,6))
        self._draw_stock_bars(chart_card)

        # Activity feed
        feed_card = make_card(mid)
        feed_card.grid(row=0, column=1, sticky="nsew")
        tk.Label(feed_card, text="Live activity",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,6))
        self._draw_activity_feed(feed_card)

        # ── BOTTOM ROW: Expiry warnings + quick actions ──
        bot = tk.Frame(inner, bg=C["bg"])
        bot.pack(fill="x", padx=20, pady=(4,20))
        bot.columnconfigure(0, weight=1)
        bot.columnconfigure(1, weight=1)

        exp_card = make_card(bot)
        exp_card.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        tk.Label(exp_card, text="Expiry warnings",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,6))
        self._draw_expiry_warnings(exp_card)

        qa_card = make_card(bot)
        qa_card.grid(row=0, column=1, sticky="nsew")
        tk.Label(qa_card, text="Quick actions",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,6))
        self._draw_quick_actions(qa_card)

    def _draw_stock_bars(self, parent):
        c = tk.Canvas(parent, bg=C["card"], height=220,
                      highlightthickness=0)
        c.pack(fill="x", padx=12, pady=(0,12))
        c.update_idletasks()
        W = c.winfo_width() or 420
        H = 220
        n = len(PRODUCTS)
        bar_h = 22
        gap = 10
        max_qty = max(p["qty"] for p in PRODUCTS) or 1
        label_w = 100

        for i, p in enumerate(PRODUCTS):
            y = 10 + i * (bar_h + gap)
            # product name
            c.create_text(label_w - 6, y + bar_h // 2,
                          text=p["name"], anchor="e",
                          font=("Segoe UI", 9), fill=C["text"])
            # background track
            c.create_rectangle(label_w, y, W - 60, y + bar_h,
                                fill="#EFF4F0", outline="")
            # bar
            ratio = p["qty"] / max_qty
            bw = int((W - 60 - label_w) * ratio)
            # color by category
            colors = {"Vegetable": C["primary"], "Fruit": C["teal"],
                      "Dairy": C["info"], "Bakery": C["warning"],
                      "Grain": C["purple"]}
            col = colors.get(p["category"], C["accent"])
            if p["qty"] < p["safety"]:
                col = C["danger"]
            c.create_rectangle(label_w, y, label_w + bw, y + bar_h,
                                fill=col, outline="")
            # safety line
            sx = label_w + int((W - 60 - label_w) * p["safety"] / max_qty)
            c.create_line(sx, y - 2, sx, y + bar_h + 2,
                          fill=C["warning"], width=2, dash=(4, 2))
            # qty label
            c.create_text(W - 58, y + bar_h // 2,
                          text=f"{p['qty']} {p['unit']}",
                          anchor="w", font=("Segoe UI", 8), fill=C["muted"])

        # legend
        ly = H - 18
        items = [("■ On track", C["primary"]),
                 ("■ Below safety", C["danger"]),
                 ("| Safety level", C["warning"])]
        lx = label_w
        for txt, col in items:
            c.create_text(lx, ly, text=txt, anchor="w",
                          font=("Segoe UI", 8), fill=col)
            lx += 130

    def _draw_activity_feed(self, parent):
        colors = {"critical": C["danger"], "warning": C["warning"],
                  "info": C["success"], "suggest": C["purple"]}
        icons  = {"critical": "●", "warning": "●",
                  "info": "●", "suggest": "◆"}
        for a in ALERTS[:6]:
            row = tk.Frame(parent, bg=C["card"])
            row.pack(fill="x", padx=12, pady=2)
            col = colors.get(a["type"], C["muted"])
            tk.Label(row, text=icons[a["type"]], bg=C["card"],
                     fg=col, font=("Segoe UI", 10)).pack(side="left")
            msg_frame = tk.Frame(row, bg=C["card"])
            msg_frame.pack(side="left", fill="x", expand=True, padx=6)
            tk.Label(msg_frame, text=a["msg"], bg=C["card"],
                     fg=C["text"], font=FONTS["small"],
                     wraplength=260, justify="left",
                     anchor="w").pack(anchor="w")
            tk.Label(msg_frame, text=a["time"], bg=C["card"],
                     fg=C["muted"], font=FONTS["small"]).pack(anchor="w")
        tk.Frame(parent, bg=C["card"], height=6).pack()

    def _draw_expiry_warnings(self, parent):
        headers = ["Product", "Qty", "Expires in", "Action"]
        col_w = [100, 60, 80, 100]
        hrow = tk.Frame(parent, bg="#EFF4F0")
        hrow.pack(fill="x", padx=12)
        for h, w in zip(headers, col_w):
            tk.Label(hrow, text=h, bg="#EFF4F0", fg=C["muted"],
                     font=("Segoe UI", 8, "bold"),
                     width=w // 8, anchor="w").pack(side="left", padx=4, pady=4)

        for p in PRODUCTS:
            days_left = p["shelf"] - p["age"]
            if days_left > 4: continue
            col = C["danger"] if days_left <= 1 else C["warning"]
            row = tk.Frame(parent, bg=C["card"])
            row.pack(fill="x", padx=12, pady=1)
            vals = [p["name"], f"{p['qty']} {p['unit']}",
                    f"{days_left} day{'s' if days_left != 1 else ''}"]
            for v, w in zip(vals, col_w[:3]):
                tk.Label(row, text=v, bg=C["card"], fg=col,
                         font=FONTS["small"], anchor="w",
                         width=w // 8).pack(side="left", padx=4, pady=3)
            tk.Button(row, text="Discount", bg=C["amb_bg"], fg=C["warning"],
                      font=("Segoe UI", 8, "bold"), relief="flat",
                      padx=6, pady=1,
                      cursor="hand2",
                      command=lambda n=p["name"]: messagebox.showinfo(
                          "Apply Discount", f"Discount applied to {n}!")
                      ).pack(side="left", padx=4)
        tk.Frame(parent, bg=C["card"], height=6).pack()

    def _draw_quick_actions(self, parent):
        actions = [
            ("+ Record Delivery",   C["primary"],  C["grn_bg"], "Record a new inbound delivery"),
            ("+ Record Sale",       C["teal"],     C["blu_bg"], "Log units sold to a buyer"),
            ("⚠ Mark as Spoiled",   C["danger"],   C["red_bg"], "Log spoiled or damaged stock"),
            ("↺ Trigger Reorder",   C["warning"],  C["amb_bg"], "Place a reorder for any product"),
            ("📊 Run Simulation",   C["purple"],   C["pur_bg"], "Open stochastic analysis"),
        ]
        for label, fg, bg, tip in actions:
            btn = tk.Button(parent, text=label,
                            bg=bg, fg=fg,
                            font=("Segoe UI", 10, "bold"),
                            relief="flat", anchor="w",
                            padx=14, pady=8, cursor="hand2",
                            command=lambda t=tip: messagebox.showinfo("Action", t))
            btn.pack(fill="x", padx=12, pady=3)
        tk.Frame(parent, bg=C["card"], height=6).pack()

    # ══════════════════════════════════════════
    #  PAGE: STOCK TRACKER
    # ══════════════════════════════════════════

    def _page_stock(self):
        cf = self.content_frame

        # Title + search row
        top = tk.Frame(cf, bg=C["bg"])
        top.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(top, text="Stock Tracker", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(side="left")

        search_var = tk.StringVar()
        search_entry = tk.Entry(top, textvariable=search_var,
                                font=FONTS["body"], width=22,
                                bg="white", fg=C["text"],
                                relief="solid", bd=1)
        search_entry.insert(0, "Search products…")
        search_entry.pack(side="right", ipady=4)

        cat_var = tk.StringVar(value="All")
        cats = ["All", "Vegetable", "Fruit", "Dairy", "Bakery", "Grain"]
        cat_menu = ttk.Combobox(top, textvariable=cat_var,
                                values=cats, state="readonly",
                                width=12, font=FONTS["body"])
        cat_menu.pack(side="right", padx=8)

        # Summary mini-cards
        sumrow = tk.Frame(cf, bg=C["bg"])
        sumrow.pack(fill="x", padx=20, pady=(0, 8))
        total_products = len(PRODUCTS)
        low_stock = sum(1 for p in PRODUCTS if p["qty"] < p["safety"])
        expiring_soon = sum(1 for p in PRODUCTS if (p["shelf"] - p["age"]) <= 2)
        for lbl, val, col in [
            ("Total products", str(total_products), C["primary"]),
            ("Low stock",      str(low_stock),      C["danger"]),
            ("Expiring ≤2d",   str(expiring_soon),  C["warning"]),
            ("All locations",  "4 zones",           C["info"]),
        ]:
            sumrow.columnconfigure(sumrow.winfo_children().__len__(), weight=1)
            c = make_card(sumrow)
            c.pack(side="left", expand=True, fill="x", padx=4)
            tk.Label(c, text=lbl, bg=C["card"], fg=C["muted"],
                     font=FONTS["small"]).pack(anchor="w", padx=10, pady=(6,0))
            tk.Label(c, text=val, bg=C["card"], fg=col,
                     font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=10, pady=(0,6))

        # Table header
        table_card = make_card(cf)
        table_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        cols = ["Product", "Category", "Qty", "Freshness", "Location", "Supplier", "Status", "Actions"]
        col_w = [120, 90, 70, 140, 110, 110, 80, 120]

        hrow = tk.Frame(table_card, bg="#EFF4F0")
        hrow.pack(fill="x")
        for h, w in zip(cols, col_w):
            tk.Label(hrow, text=h, bg="#EFF4F0", fg=C["muted"],
                     font=("Segoe UI", 8, "bold"),
                     width=w // 8, anchor="w").pack(side="left", padx=6, pady=6)

        # Scrollable rows
        scroll_frame = tk.Frame(table_card, bg=C["card"])
        scroll_frame.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(scroll_frame, orient="vertical")
        vsb.pack(side="right", fill="y")
        inner_c = tk.Canvas(scroll_frame, bg=C["card"],
                            highlightthickness=0,
                            yscrollcommand=vsb.set)
        inner_c.pack(fill="both", expand=True)
        vsb.config(command=inner_c.yview)
        rows_frame = tk.Frame(inner_c, bg=C["card"])
        inner_c.create_window((0, 0), window=rows_frame, anchor="nw")
        rows_frame.bind("<Configure>",
                        lambda e: inner_c.configure(
                            scrollregion=inner_c.bbox("all")))

        for p in PRODUCTS:
            days_left = p["shelf"] - p["age"]
            low = p["qty"] < p["safety"]
            row_bg = C["red_bg"] if days_left <= 1 else C["card"]

            row = tk.Frame(rows_frame, bg=row_bg,
                           highlightthickness=1,
                           highlightbackground=C["border"])
            row.pack(fill="x", pady=1)

            # Product name
            tk.Label(row, text=p["name"], bg=row_bg, fg=C["text"],
                     font=("Segoe UI", 10, "bold"),
                     width=col_w[0]//8, anchor="w").pack(side="left", padx=6, pady=8)
            # Category badge
            cat_cols = {"Vegetable": (C["grn_bg"], C["primary"]),
                        "Fruit":     (C["blu_bg"],  C["info"]),
                        "Dairy":     (C["pur_bg"],  C["purple"]),
                        "Bakery":    (C["amb_bg"],  C["warning"]),
                        "Grain":     ("#F5F0E8",    "#7D6608")}
            cbg, cfg = cat_cols.get(p["category"], (C["card"], C["muted"]))
            cat_lbl = tk.Label(row, text=p["category"], bg=cbg, fg=cfg,
                               font=("Segoe UI", 8, "bold"),
                               padx=6, pady=1)
            cat_lbl.pack(side="left", padx=6)

            # Qty
            qty_col = C["danger"] if low else C["text"]
            tk.Label(row, text=f"{p['qty']} {p['unit']}", bg=row_bg, fg=qty_col,
                     font=("Segoe UI", 10, "bold"),
                     width=col_w[2]//8, anchor="w").pack(side="left", padx=6)

            # Freshness bar
            fc = tk.Canvas(row, bg=row_bg, highlightthickness=0,
                           width=130, height=14)
            fc.pack(side="left", padx=6, pady=6)
            draw_freshness(fc, p["age"], p["shelf"], 130, 14)

            # Location
            tk.Label(row, text=p["location"], bg=row_bg, fg=C["muted"],
                     font=FONTS["small"],
                     width=col_w[4]//8, anchor="w").pack(side="left", padx=6)
            # Supplier
            tk.Label(row, text=p["supplier"], bg=row_bg, fg=C["muted"],
                     font=FONTS["small"],
                     width=col_w[5]//8, anchor="w").pack(side="left", padx=6)

            # Status pill
            if days_left <= 1:
                s_text, s_bg, s_fg = "Expiring!", C["red_bg"], C["danger"]
            elif low:
                s_text, s_bg, s_fg = "Low stock", C["amb_bg"], C["warning"]
            else:
                s_text, s_bg, s_fg = "Good", C["grn_bg"], C["success"]
            tk.Label(row, text=s_text, bg=s_bg, fg=s_fg,
                     font=("Segoe UI", 8, "bold"),
                     padx=6, pady=2).pack(side="left", padx=6)

            # Action buttons
            act_frame = tk.Frame(row, bg=row_bg)
            act_frame.pack(side="left", padx=4)
            tk.Button(act_frame, text="Sell", bg=C["grn_bg"], fg=C["primary"],
                      font=("Segoe UI", 8, "bold"), relief="flat", padx=6, pady=2,
                      cursor="hand2",
                      command=lambda n=p["name"]: messagebox.showinfo(
                          "Record Sale", f"Recording sale for {n}")
                      ).pack(side="left", padx=2)
            tk.Button(act_frame, text="Order", bg=C["blu_bg"], fg=C["info"],
                      font=("Segoe UI", 8, "bold"), relief="flat", padx=6, pady=2,
                      cursor="hand2",
                      command=lambda n=p["name"]: messagebox.showinfo(
                          "Reorder", f"Reorder triggered for {n}")
                      ).pack(side="left", padx=2)

    # ══════════════════════════════════════════
    #  PAGE: ORDERS
    # ══════════════════════════════════════════

    def _page_orders(self):
        cf = self.content_frame
        tk.Label(cf, text="Orders & Supply", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(anchor="w", padx=20, pady=(16,8))

        two = tk.Frame(cf, bg=C["bg"])
        two.pack(fill="both", expand=True, padx=20, pady=(0,20))
        two.columnconfigure(0, weight=1)
        two.columnconfigure(1, weight=1)

        # Inbound
        in_card = make_card(two)
        in_card.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        tk.Label(in_card, text="Inbound deliveries (from suppliers)",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))

        tk.Button(in_card, text="+ Record delivery",
                  bg=C["grn_bg"], fg=C["primary"],
                  font=("Segoe UI", 9, "bold"), relief="flat",
                  padx=10, pady=4, cursor="hand2",
                  command=lambda: messagebox.showinfo(
                      "Record Delivery", "Open delivery form")).pack(
                      anchor="e", padx=12, pady=(0,6))

        hdrs = ["Supplier", "Product", "Qty", "ETA", "Status"]
        hrow = tk.Frame(in_card, bg="#EFF4F0")
        hrow.pack(fill="x", padx=12)
        for h in hdrs:
            tk.Label(hrow, text=h, bg="#EFF4F0", fg=C["muted"],
                     font=("Segoe UI", 8, "bold"),
                     width=10, anchor="w").pack(side="left", padx=4, pady=4)

        status_styles = {
            "On the way": (C["grn_bg"], C["success"]),
            "Confirmed":  (C["blu_bg"], C["info"]),
            "Scheduled":  (C["amb_bg"], C["warning"]),
            "Delayed":    (C["red_bg"], C["danger"]),
        }
        for o in ORDERS_IN:
            row = tk.Frame(in_card, bg=C["card"],
                           highlightthickness=1,
                           highlightbackground=C["border"])
            row.pack(fill="x", padx=12, pady=1)
            for val in [o["supplier"], o["product"], o["qty"], o["eta"]]:
                tk.Label(row, text=val, bg=C["card"], fg=C["text"],
                         font=FONTS["small"], width=10,
                         anchor="w").pack(side="left", padx=4, pady=6)
            sbg, sfg = status_styles.get(o["status"], (C["card"], C["muted"]))
            tk.Label(row, text=o["status"], bg=sbg, fg=sfg,
                     font=("Segoe UI", 8, "bold"),
                     padx=6, pady=1).pack(side="left", padx=4)

        # Outbound
        out_card = make_card(two)
        out_card.grid(row=0, column=1, sticky="nsew")
        tk.Label(out_card, text="Outbound sales (to buyers)",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))

        tk.Button(out_card, text="+ Record sale",
                  bg=C["blu_bg"], fg=C["info"],
                  font=("Segoe UI", 9, "bold"), relief="flat",
                  padx=10, pady=4, cursor="hand2",
                  command=lambda: messagebox.showinfo(
                      "Record Sale", "Open sale form")).pack(
                      anchor="e", padx=12, pady=(0,6))

        hdrs2 = ["Buyer", "Product", "Qty", "Date", "Status"]
        hrow2 = tk.Frame(out_card, bg="#EFF4F0")
        hrow2.pack(fill="x", padx=12)
        for h in hdrs2:
            tk.Label(hrow2, text=h, bg="#EFF4F0", fg=C["muted"],
                     font=("Segoe UI", 8, "bold"),
                     width=10, anchor="w").pack(side="left", padx=4, pady=4)

        out_styles = {
            "Fulfilled": (C["grn_bg"], C["success"]),
            "Pending":   (C["amb_bg"], C["warning"]),
            "Confirmed": (C["blu_bg"], C["info"]),
            "Shortfall": (C["red_bg"], C["danger"]),
        }
        for o in ORDERS_OUT:
            row = tk.Frame(out_card, bg=C["card"],
                           highlightthickness=1,
                           highlightbackground=C["border"])
            row.pack(fill="x", padx=12, pady=1)
            for val in [o["buyer"], o["product"], o["qty"], o["date"]]:
                tk.Label(row, text=val, bg=C["card"], fg=C["text"],
                         font=FONTS["small"], width=10,
                         anchor="w").pack(side="left", padx=4, pady=6)
            sbg, sfg = out_styles.get(o["status"], (C["card"], C["muted"]))
            tk.Label(row, text=o["status"], bg=sbg, fg=sfg,
                     font=("Segoe UI", 8, "bold"),
                     padx=6, pady=1).pack(side="left", padx=4)

    # ══════════════════════════════════════════
    #  PAGE: ALERTS
    # ══════════════════════════════════════════

    def _page_alerts(self):
        cf = self.content_frame
        tk.Label(cf, text="Alerts", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(anchor="w", padx=20, pady=(16,8))

        # Filter buttons
        frow = tk.Frame(cf, bg=C["bg"])
        frow.pack(fill="x", padx=20, pady=(0,10))
        filters = [("All", "#888"), ("Critical", C["danger"]),
                   ("Warning", C["warning"]), ("Info", C["success"]),
                   ("Suggestions", C["purple"])]
        for label, col in filters:
            tk.Button(frow, text=label, bg=C["card"], fg=col,
                      font=("Segoe UI", 9, "bold"), relief="solid",
                      bd=1, padx=10, pady=4, cursor="hand2").pack(
                      side="left", padx=4)

        card = make_card(cf)
        card.pack(fill="both", expand=True, padx=20, pady=(0,20))

        type_styles = {
            "critical": (C["red_bg"], C["danger"],  "CRITICAL", "●"),
            "warning":  (C["amb_bg"], C["warning"], "WARNING",  "▲"),
            "info":     (C["grn_bg"], C["success"], "INFO",     "✓"),
            "suggest":  (C["pur_bg"], C["purple"],  "TIP",      "◆"),
        }

        for a in ALERTS:
            bg, fg, tag, icon = type_styles[a["type"]]
            row = tk.Frame(card, bg=bg,
                           highlightthickness=1,
                           highlightbackground=C["border"])
            row.pack(fill="x", padx=12, pady=3)

            # Icon + tag
            left = tk.Frame(row, bg=bg, width=80)
            left.pack(side="left", fill="y", padx=8, pady=8)
            left.pack_propagate(False)
            tk.Label(left, text=icon, bg=bg, fg=fg,
                     font=("Segoe UI", 14)).pack()
            tk.Label(left, text=tag, bg=bg, fg=fg,
                     font=("Segoe UI", 7, "bold")).pack()

            # Message
            mid = tk.Frame(row, bg=bg)
            mid.pack(side="left", fill="x", expand=True, pady=8)
            tk.Label(mid, text=a["msg"], bg=bg, fg=C["text"],
                     font=("Segoe UI", 10),
                     wraplength=600, justify="left",
                     anchor="w").pack(anchor="w")
            tk.Label(mid, text=a["time"], bg=bg, fg=C["muted"],
                     font=FONTS["small"]).pack(anchor="w", pady=(2,0))

            # Dismiss button
            tk.Button(row, text="Dismiss", bg=bg, fg=C["muted"],
                      font=("Segoe UI", 8), relief="flat",
                      padx=10, pady=4, cursor="hand2",
                      command=lambda r=row: r.destroy()
                      ).pack(side="right", padx=8)

    # ══════════════════════════════════════════
    #  PAGE: ANALYSIS
    # ══════════════════════════════════════════

    def _page_analysis(self):
        cf = self.content_frame
        tk.Label(cf, text="Analysis", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(anchor="w", padx=20, pady=(16,8))

        two = tk.Frame(cf, bg=C["bg"])
        two.pack(fill="both", expand=True, padx=20, pady=(0,20))
        two.columnconfigure(0, weight=1)
        two.columnconfigure(1, weight=1)
        two.rowconfigure(0, weight=1)
        two.rowconfigure(1, weight=1)

        # Chart 1: supply vs demand (simulated)
        c1 = make_card(two)
        c1.grid(row=0, column=0, padx=(0,8), pady=(0,8), sticky="nsew")
        tk.Label(c1, text="Supply vs Demand — last 30 days",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        self._chart_supply_demand(c1)

        # Chart 2: waste per product
        c2 = make_card(two)
        c2.grid(row=0, column=1, pady=(0,8), sticky="nsew")
        tk.Label(c2, text="Waste by product this month (kg)",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        self._chart_waste(c2)

        # Chart 3: service level
        c3 = make_card(two)
        c3.grid(row=1, column=0, padx=(0,8), sticky="nsew")
        tk.Label(c3, text="Service level % — last 8 weeks",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        self._chart_service_level(c3)

        # KPIs summary
        c4 = make_card(two)
        c4.grid(row=1, column=1, sticky="nsew")
        tk.Label(c4, text="Performance summary",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        self._kpi_summary(c4)

    def _chart_supply_demand(self, parent):
        canvas = tk.Canvas(parent, bg=C["card"], height=180,
                           highlightthickness=0)
        canvas.pack(fill="x", padx=12, pady=(0,12))
        canvas.update_idletasks()
        W = canvas.winfo_width() or 360
        H = 180
        L, R, T, B = 30, 10, 15, 30

        # Simulated data
        _seed_bak = globals()["_seed"]
        supply  = [rand_int(60, 130) for _ in range(30)]
        demand  = [rand_int(70, 120) for _ in range(30)]
        globals()["_seed"] = _seed_bak

        all_v = supply + demand
        lo, hi = min(all_v) - 5, max(all_v) + 5

        def px(i): return L + i / 29 * (W - L - R)
        def py(v): return T + (1 - (v - lo) / (hi - lo)) * (H - T - B)

        # Grid
        for k in range(4):
            gv = lo + k * (hi - lo) / 3
            gy = py(gv)
            canvas.create_line(L, gy, W - R, gy, fill=C["border"], dash=(3,3))
            canvas.create_text(L - 4, gy, text=str(int(gv)), anchor="e",
                               font=("Segoe UI", 7), fill=C["muted"])

        # Supply line (green)
        pts = []
        for i, v in enumerate(supply): pts += [px(i), py(v)]
        canvas.create_line(pts, fill=C["primary"], width=2, smooth=True)

        # Demand line (amber dashed)
        pts2 = []
        for i, v in enumerate(demand): pts2 += [px(i), py(v)]
        canvas.create_line(pts2, fill=C["warning"], width=2,
                           smooth=True, dash=(5, 3))

        # Axes
        canvas.create_line(L, T, L, H - B, fill=C["border"])
        canvas.create_line(L, H - B, W - R, H - B, fill=C["border"])

        # Legend
        canvas.create_line(L, H - 10, L + 20, H - 10,
                           fill=C["primary"], width=2)
        canvas.create_text(L + 24, H - 10, text="Supply",
                           anchor="w", font=("Segoe UI", 8), fill=C["primary"])
        canvas.create_line(L + 80, H - 10, L + 100, H - 10,
                           fill=C["warning"], width=2, dash=(4, 2))
        canvas.create_text(L + 104, H - 10, text="Demand",
                           anchor="w", font=("Segoe UI", 8), fill=C["warning"])

    def _chart_waste(self, parent):
        canvas = tk.Canvas(parent, bg=C["card"], height=180,
                           highlightthickness=0)
        canvas.pack(fill="x", padx=12, pady=(0,12))
        canvas.update_idletasks()
        W = canvas.winfo_width() or 360
        H = 180
        waste = [rand_int(1, 18) for _ in PRODUCTS]
        max_w = max(waste) or 1
        n = len(PRODUCTS)
        bar_w = max(12, (W - 40) // n - 8)
        colors = [C["primary"], C["teal"], C["info"], C["purple"],
                  C["warning"], C["primary"], C["teal"], C["info"]]

        for i, (p, w) in enumerate(zip(PRODUCTS, waste)):
            x = 20 + i * ((W - 40) // n)
            bh = int(w / max_w * (H - 50))
            y = H - 30 - bh
            canvas.create_rectangle(x, y, x + bar_w, H - 30,
                                    fill=colors[i % len(colors)], outline="")
            canvas.create_text(x + bar_w // 2, H - 18,
                               text=p["name"][:5], anchor="n",
                               font=("Segoe UI", 7), fill=C["muted"])
            canvas.create_text(x + bar_w // 2, y - 4,
                               text=str(w),
                               font=("Segoe UI", 7, "bold"), fill=C["text"])

        canvas.create_line(20, 10, 20, H - 30, fill=C["border"])
        canvas.create_line(20, H - 30, W - 10, H - 30, fill=C["border"])

    def _chart_service_level(self, parent):
        canvas = tk.Canvas(parent, bg=C["card"], height=180,
                           highlightthickness=0)
        canvas.pack(fill="x", padx=12, pady=(0,12))
        canvas.update_idletasks()
        W = canvas.winfo_width() or 360
        H = 180
        L, R, T, B = 30, 10, 15, 30

        weeks = [rand_int(85, 98) for _ in range(8)]
        lo, hi = 75, 100

        def px(i): return L + i / 7 * (W - L - R)
        def py(v): return T + (1 - (v - lo) / (hi - lo)) * (H - T - B)

        # 90% target line
        ty = py(90)
        canvas.create_line(L, ty, W - R, ty,
                           fill=C["warning"], dash=(5, 3), width=1)
        canvas.create_text(W - R - 2, ty - 6, text="90% target",
                           anchor="e", font=("Segoe UI", 7), fill=C["warning"])

        # Fill area under line
        pts_fill = [L, H - B]
        for i, v in enumerate(weeks): pts_fill += [px(i), py(v)]
        pts_fill += [px(7), H - B]
        canvas.create_polygon(pts_fill, fill="#EAFAF1", outline="")

        # Line
        pts = []
        for i, v in enumerate(weeks): pts += [px(i), py(v)]
        canvas.create_line(pts, fill=C["success"], width=2, smooth=True)

        # Dots + labels
        for i, v in enumerate(weeks):
            canvas.create_oval(px(i)-3, py(v)-3, px(i)+3, py(v)+3,
                               fill=C["success"], outline="white", width=1)
            canvas.create_text(px(i), H - 18, text=f"W{i+1}",
                               font=("Segoe UI", 7), fill=C["muted"])

        # Y axis labels
        for k in range(4):
            gv = lo + k * (hi - lo) / 3
            canvas.create_text(L - 4, py(gv), text=f"{int(gv)}%",
                               anchor="e", font=("Segoe UI", 7), fill=C["muted"])

        canvas.create_line(L, T, L, H - B, fill=C["border"])
        canvas.create_line(L, H - B, W - R, H - B, fill=C["border"])

    def _kpi_summary(self, parent):
        metrics = [
            ("Avg service level",    "93.8%",  C["success"], "Last 8 weeks"),
            ("Total waste",          "62 kg",  C["danger"],  "This month"),
            ("Avg daily profit",     "₹4,820", C["primary"], "Across all products"),
            ("Stockout incidents",   "7",      C["warning"], "This month"),
            ("Top wasted product",   "Spinach",C["danger"],  "Due to short shelf life"),
            ("Best service product", "Potatoes",C["success"],"100% fulfilled"),
        ]
        for lbl, val, col, note in metrics:
            row = tk.Frame(parent, bg=C["card"])
            row.pack(fill="x", padx=12, pady=4)
            tk.Label(row, text=lbl, bg=C["card"], fg=C["muted"],
                     font=FONTS["small"], width=22, anchor="w").pack(side="left")
            tk.Label(row, text=val, bg=C["card"], fg=col,
                     font=("Segoe UI", 11, "bold")).pack(side="left", padx=8)
            tk.Label(row, text=note, bg=C["card"], fg=C["muted"],
                     font=FONTS["small"]).pack(side="left")
        tk.Frame(parent, bg=C["card"], height=6).pack()

    # ══════════════════════════════════════════
    #  PAGE: SETTINGS
    # ══════════════════════════════════════════

    def _page_settings(self):
        cf = self.content_frame
        tk.Label(cf, text="Settings", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(anchor="w", padx=20, pady=(16,8))

        scroll_c = tk.Canvas(cf, bg=C["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(cf, orient="vertical", command=scroll_c.yview)
        scroll_c.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        scroll_c.pack(fill="both", expand=True)
        inner = tk.Frame(scroll_c, bg=C["bg"])
        wid = scroll_c.create_window((0,0), window=inner, anchor="nw")
        scroll_c.bind("<Configure>", lambda e: scroll_c.itemconfig(wid, width=e.width))
        inner.bind("<Configure>", lambda e: scroll_c.configure(
            scrollregion=scroll_c.bbox("all")))

        two = tk.Frame(inner, bg=C["bg"])
        two.pack(fill="x", padx=20, pady=(0,12))
        two.columnconfigure(0, weight=1)
        two.columnconfigure(1, weight=1)

        # Product settings
        prod_card = make_card(two)
        prod_card.grid(row=0, column=0, padx=(0,8), pady=(0,8), sticky="nsew")
        tk.Label(prod_card, text="Product thresholds",
                 bg=C["card"], fg=C["text"], font=FONTS["h3"]).pack(
                     anchor="w", padx=12, pady=(10,6))

        hdrs = ["Product", "Safety stock", "Reorder qty", "Shelf life"]
        hrow = tk.Frame(prod_card, bg="#EFF4F0")
        hrow.pack(fill="x", padx=12)
        for h in hdrs:
            tk.Label(hrow, text=h, bg="#EFF4F0", fg=C["muted"],
                     font=("Segoe UI", 8, "bold"),
                     width=11, anchor="w").pack(side="left", padx=4, pady=4)

        for p in PRODUCTS:
            row = tk.Frame(prod_card, bg=C["card"],
                           highlightthickness=1,
                           highlightbackground=C["border"])
            row.pack(fill="x", padx=12, pady=1)
            tk.Label(row, text=p["name"], bg=C["card"], fg=C["text"],
                     font=("Segoe UI", 9, "bold"),
                     width=11, anchor="w").pack(side="left", padx=4, pady=6)
            for key in ["safety", "reorder", "shelf"]:
                e = tk.Entry(row, bg="#F8FAF5", fg=C["text"],
                             font=FONTS["small"], width=7,
                             relief="solid", bd=1)
                e.insert(0, str(p[key]))
                e.pack(side="left", padx=8)

        tk.Button(prod_card, text="Save changes",
                  bg=C["primary"], fg="white",
                  font=("Segoe UI", 9, "bold"), relief="flat",
                  padx=14, pady=6, cursor="hand2",
                  command=lambda: messagebox.showinfo(
                      "Saved", "Product settings saved successfully!")
                  ).pack(anchor="e", padx=12, pady=10)

        # System settings
        sys_card = make_card(two)
        sys_card.grid(row=0, column=1, pady=(0,8), sticky="nsew")
        tk.Label(sys_card, text="System preferences",
                 bg=C["card"], fg=C["text"], font=FONTS["h3"]).pack(
                     anchor="w", padx=12, pady=(10,6))

        fields = [
            ("Hub name",             "Fresh Produce Hub"),
            ("Default currency",     "INR (₹)"),
            ("Critical alert (days)", "1"),
            ("Warning alert (days)",  "3"),
            ("Default unit",          "kg"),
        ]
        for lbl, default in fields:
            row = tk.Frame(sys_card, bg=C["card"])
            row.pack(fill="x", padx=12, pady=4)
            tk.Label(row, text=lbl, bg=C["card"], fg=C["muted"],
                     font=FONTS["small"], width=22, anchor="w").pack(side="left")
            e = tk.Entry(row, bg="#F8FAF5", fg=C["text"],
                         font=FONTS["body"], width=18,
                         relief="solid", bd=1)
            e.insert(0, default)
            e.pack(side="right")

        tk.Label(sys_card, text="Notification channels",
                 bg=C["card"], fg=C["muted"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=12, pady=(12,4))
        for ch in ["In-app alerts", "SMS / WhatsApp", "Email digest"]:
            v = tk.BooleanVar(value=True)
            tk.Checkbutton(sys_card, text=ch, variable=v,
                           bg=C["card"], fg=C["text"],
                           font=FONTS["body"],
                           activebackground=C["card"],
                           selectcolor=C["primary"]).pack(anchor="w", padx=12)

        tk.Button(sys_card, text="Save preferences",
                  bg=C["primary"], fg="white",
                  font=("Segoe UI", 9, "bold"), relief="flat",
                  padx=14, pady=6, cursor="hand2",
                  command=lambda: messagebox.showinfo(
                      "Saved", "Preferences saved successfully!")
                  ).pack(anchor="e", padx=12, pady=10)

    # ── CLOCK ────────────────────────────────

    def _start_clock(self):
        def tick():
            self.clock_var.set(time.strftime("  %a %d %b %Y   %I:%M:%S %p  "))
            self.root.after(1000, tick)
        tick()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    style_root = tk.Tk()
    style_root.withdraw()

    root = tk.Toplevel(style_root)
    root.protocol("WM_DELETE_WINDOW", style_root.destroy)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TCombobox",
                    fieldbackground="white", background="white",
                    foreground=C["text"], selectbackground=C["primary"],
                    selectforeground="white", arrowcolor=C["muted"])
    style.map("TCombobox", fieldbackground=[("readonly", "white")])
    style.configure("TScrollbar", background=C["border"],
                    troughcolor=C["bg"], arrowcolor=C["muted"])

    app = AgriInventoryApp(root)
    style_root.mainloop()