"""
=============================================================
  AGRICULTURAL GOODS INVENTORY MANAGEMENT SYSTEM
  Using Stochastic Analysis & Monte Carlo Simulation
  Built with Python, Tkinter (UI), and OOP Design
=============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import numpy as np
import random
import sqlite3
import datetime
import threading
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")

# ─────────────────────────────────────────────
#  OOP CLASS 1: Product
# ─────────────────────────────────────────────
class Product:
    """Represents an agricultural product with stochastic properties."""

    def __init__(self, product_id, name, category, shelf_life_days,
                 current_stock, reorder_point, unit_cost, unit="kg"):
        self.product_id = product_id
        self.name = name
        self.category = category
        self.shelf_life_days = shelf_life_days
        self.current_stock = current_stock
        self.reorder_point = reorder_point
        self.unit_cost = unit_cost
        self.unit = unit
        self.added_date = datetime.date.today()

    def needs_reorder(self):
        """Check if stock has fallen below reorder point."""
        return self.current_stock <= self.reorder_point

    def is_expiring_soon(self, days_threshold=3):
        """Check if product will expire within threshold days."""
        return self.shelf_life_days <= days_threshold

    def consume(self, quantity):
        """Consume stock. Returns True if successful."""
        if quantity <= self.current_stock:
            self.current_stock -= quantity
            return True
        return False

    def restock(self, quantity):
        """Add stock."""
        self.current_stock += quantity

    def get_status(self):
        if self.current_stock == 0:
            return "OUT OF STOCK"
        elif self.needs_reorder():
            return "LOW STOCK"
        elif self.is_expiring_soon():
            return "EXPIRING SOON"
        else:
            return "HEALTHY"

    def __str__(self):
        return f"Product({self.name}, Stock: {self.current_stock} {self.unit})"


# ─────────────────────────────────────────────
#  OOP CLASS 2: PerishableProduct (Inheritance)
# ─────────────────────────────────────────────
class PerishableProduct(Product):
    """Extends Product with spoilage rate modeling."""

    def __init__(self, product_id, name, category, shelf_life_days,
                 current_stock, reorder_point, unit_cost,
                 spoilage_rate=0.05, unit="kg"):
        super().__init__(product_id, name, category, shelf_life_days,
                         current_stock, reorder_point, unit_cost, unit)
        self.spoilage_rate = spoilage_rate  # daily % spoilage

    def calculate_daily_spoilage(self):
        """Calculate how much stock spoils each day (stochastic)."""
        rate = np.random.normal(self.spoilage_rate, self.spoilage_rate * 0.2)
        rate = max(0, min(rate, 1))
        return self.current_stock * rate

    def apply_spoilage(self):
        """Apply daily spoilage to current stock."""
        spoiled = self.calculate_daily_spoilage()
        self.current_stock = max(0, self.current_stock - spoiled)
        return spoiled


# ─────────────────────────────────────────────
#  OOP CLASS 3: StochasticDemandModel
# ─────────────────────────────────────────────
class StochasticDemandModel:
    """Models stochastic (random) demand using statistical distributions."""

    DISTRIBUTION_NORMAL = "normal"
    DISTRIBUTION_POISSON = "poisson"

    def __init__(self, mean_demand, std_demand=None, distribution="normal"):
        self.mean_demand = mean_demand
        self.std_demand = std_demand or mean_demand * 0.3
        self.distribution = distribution

    def simulate_demand(self, days=1):
        """Simulate demand for given number of days."""
        demands = []
        for _ in range(days):
            if self.distribution == self.DISTRIBUTION_NORMAL:
                d = np.random.normal(self.mean_demand, self.std_demand)
            else:
                d = np.random.poisson(self.mean_demand)
            demands.append(max(0, d))
        return demands

    def simulate_lead_time(self, mean_lead=3, std_lead=1):
        """Simulate lead time (days for resupply) stochastically."""
        return max(1, int(np.random.normal(mean_lead, std_lead)))

    def get_reorder_point(self, mean_lead=3, std_lead=1, service_level=0.95):
        """Calculate optimal reorder point using stochastic formula."""
        z = self._get_z_score(service_level)
        avg_demand_during_lead = self.mean_demand * mean_lead
        safety_stock = z * np.sqrt(
            (mean_lead * self.std_demand**2) +
            (self.mean_demand**2 * std_lead**2)
        )
        return avg_demand_during_lead + safety_stock

    def _get_z_score(self, service_level):
        from scipy.stats import norm
        try:
            return norm.ppf(service_level)
        except ImportError:
            # fallback z-scores
            z_map = {0.90: 1.28, 0.95: 1.645, 0.99: 2.33}
            return z_map.get(service_level, 1.645)


# ─────────────────────────────────────────────
#  OOP CLASS 4: MonteCarloSimulator
# ─────────────────────────────────────────────
class MonteCarloSimulator:
    """Runs Monte Carlo simulations for inventory analysis."""

    def __init__(self, product: PerishableProduct,
                 demand_model: StochasticDemandModel,
                 num_simulations=500, time_horizon=30):
        self.product = product
        self.demand_model = demand_model
        self.num_simulations = num_simulations
        self.time_horizon = time_horizon
        self.results = []

    def run(self, progress_callback=None):
        """Run full Monte Carlo simulation."""
        self.results = []
        stockout_count = 0
        total_spoilage = 0

        for sim in range(self.num_simulations):
            stock = self.product.current_stock
            daily_stocks = [stock]
            sim_spoilage = 0
            stockout = False

            demands = self.demand_model.simulate_demand(self.time_horizon)

            for day in range(self.time_horizon):
                # Apply spoilage
                spoilage = stock * np.random.normal(
                    self.product.spoilage_rate,
                    self.product.spoilage_rate * 0.2
                ) if hasattr(self.product, 'spoilage_rate') else 0
                spoilage = max(0, spoilage)
                stock -= spoilage
                sim_spoilage += spoilage

                # Apply demand
                demand = demands[day]
                if demand > stock:
                    stockout = True
                    stock = 0
                else:
                    stock -= demand

                # Reorder check
                if stock <= self.product.reorder_point:
                    lead_time = self.demand_model.simulate_lead_time()
                    reorder_qty = self.product.reorder_point * 2
                    if day + lead_time < self.time_horizon:
                        stock += reorder_qty

                stock = max(0, stock)
                daily_stocks.append(stock)

            if stockout:
                stockout_count += 1
            total_spoilage += sim_spoilage
            self.results.append(daily_stocks)

            if progress_callback:
                progress_callback(int((sim + 1) / self.num_simulations * 100))

        return self._summarize(stockout_count, total_spoilage)

    def _summarize(self, stockout_count, total_spoilage):
        all_finals = [r[-1] for r in self.results]
        return {
            "avg_final_stock": np.mean(all_finals),
            "min_final_stock": np.min(all_finals),
            "max_final_stock": np.max(all_finals),
            "std_final_stock": np.std(all_finals),
            "stockout_probability": stockout_count / self.num_simulations * 100,
            "avg_spoilage": total_spoilage / self.num_simulations,
            "service_level": 100 - (stockout_count / self.num_simulations * 100),
            "simulations_run": self.num_simulations,
            "time_horizon": self.time_horizon
        }

    def get_percentile_paths(self):
        """Return 10th, 50th, 90th percentile stock paths."""
        arr = np.array(self.results)
        return {
            "p10": np.percentile(arr, 10, axis=0),
            "p50": np.percentile(arr, 50, axis=0),
            "p90": np.percentile(arr, 90, axis=0),
            "days": list(range(self.time_horizon + 1))
        }


# ─────────────────────────────────────────────
#  OOP CLASS 5: DatabaseManager
# ─────────────────────────────────────────────
class DatabaseManager:
    """Handles SQLite database operations."""

    def __init__(self, db_path="agri_inventory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                shelf_life INTEGER,
                current_stock REAL,
                reorder_point REAL,
                unit_cost REAL,
                spoilage_rate REAL,
                unit TEXT,
                added_date TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                product_name TEXT,
                trans_type TEXT,
                quantity REAL,
                date TEXT,
                notes TEXT
            )
        """)
        conn.commit()

        # Seed sample data if empty
        c.execute("SELECT COUNT(*) FROM products")
        if c.fetchone()[0] == 0:
            self._seed_data(c)
            conn.commit()
        conn.close()

    def _seed_data(self, cursor):
        samples = [
            ("Wheat",      "Grain",     90,  500, 100, 25.0, 0.02, "kg"),
            ("Rice",       "Grain",     180, 400, 80,  35.0, 0.01, "kg"),
            ("Tomatoes",   "Vegetable", 7,   150, 50,  18.0, 0.12, "kg"),
            ("Potatoes",   "Vegetable", 30,  300, 70,  15.0, 0.05, "kg"),
            ("Onions",     "Vegetable", 21,  250, 60,  12.0, 0.04, "kg"),
            ("Mangoes",    "Fruit",     5,   100, 40,  45.0, 0.15, "kg"),
            ("Bananas",    "Fruit",     4,   120, 50,  28.0, 0.18, "kg"),
            ("Corn",       "Grain",     14,  200, 60,  20.0, 0.08, "kg"),
            ("Spinach",    "Vegetable", 3,   80,  30,  22.0, 0.20, "kg"),
            ("Sugarcane",  "Cash Crop", 2,   350, 90,  8.0,  0.10, "kg"),
        ]
        for s in samples:
            cursor.execute("""
                INSERT INTO products (name, category, shelf_life, current_stock,
                reorder_point, unit_cost, spoilage_rate, unit, added_date)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (*s, str(datetime.date.today())))

    def get_all_products(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM products ORDER BY name")
        rows = c.fetchall()
        conn.close()
        return rows

    def add_product(self, name, category, shelf_life, stock, reorder,
                    cost, spoilage, unit):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO products (name, category, shelf_life, current_stock,
            reorder_point, unit_cost, spoilage_rate, unit, added_date)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (name, category, shelf_life, stock, reorder, cost, spoilage,
              unit, str(datetime.date.today())))
        conn.commit()
        conn.close()

    def update_stock(self, product_id, new_stock):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE products SET current_stock=? WHERE id=?",
                  (new_stock, product_id))
        conn.commit()
        conn.close()

    def delete_product(self, product_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        conn.close()

    def log_transaction(self, product_id, product_name, trans_type, qty, notes=""):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO transactions (product_id, product_name, trans_type,
            quantity, date, notes) VALUES (?,?,?,?,?,?)
        """, (product_id, product_name, trans_type, qty,
              str(datetime.datetime.now()), notes))
        conn.commit()
        conn.close()

    def get_transactions(self, limit=50):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM transactions ORDER BY date DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return rows

    def row_to_product(self, row):
        """Convert DB row to PerishableProduct object."""
        return PerishableProduct(
            product_id=row[0], name=row[1], category=row[2],
            shelf_life_days=row[3], current_stock=row[4],
            reorder_point=row[5], unit_cost=row[6],
            spoilage_rate=row[7], unit=row[8]
        )


# ─────────────────────────────────────────────
#  OOP CLASS 6: InventoryGUI (Main UI)
# ─────────────────────────────────────────────
class InventoryGUI:
    """Main Tkinter GUI Application."""

    # Color Palette — earthy/agricultural theme
    BG_DARK    = "#1a1f16"
    BG_PANEL   = "#232b1e"
    BG_CARD    = "#2d3827"
    ACCENT     = "#7ec850"
    ACCENT2    = "#f0a500"
    ACCENT3    = "#e05c3a"
    TEXT_MAIN  = "#e8f0e0"
    TEXT_DIM   = "#8a9e80"
    BTN_BG     = "#3d5c2a"
    BTN_HOVER  = "#4e7535"

    def __init__(self):
        self.db = DatabaseManager()
        self.root = tk.Tk()
        self.root.title("🌾 AgroStock — Agricultural Inventory System")
        self.root.geometry("1280x800")
        self.root.minsize(1100, 700)
        self.root.configure(bg=self.BG_DARK)

        self._setup_styles()
        self._build_layout()
        self._show_dashboard()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=self.BG_DARK,
                        foreground=self.TEXT_MAIN, font=("Consolas", 10))

        style.configure("Treeview",
                        background=self.BG_CARD,
                        foreground=self.TEXT_MAIN,
                        fieldbackground=self.BG_CARD,
                        rowheight=28, font=("Consolas", 10))
        style.configure("Treeview.Heading",
                        background=self.BG_PANEL,
                        foreground=self.ACCENT,
                        font=("Consolas", 10, "bold"))
        style.map("Treeview", background=[("selected", self.BTN_BG)])

        style.configure("TNotebook", background=self.BG_DARK,
                        borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=self.BG_PANEL,
                        foreground=self.TEXT_DIM,
                        padding=[14, 6],
                        font=("Consolas", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", self.BG_CARD)],
                  foreground=[("selected", self.ACCENT)])

        style.configure("TProgressbar",
                        troughcolor=self.BG_PANEL,
                        background=self.ACCENT,
                        thickness=12)

    def _build_layout(self):
        # ── Sidebar ──
        self.sidebar = tk.Frame(self.root, bg=self.BG_PANEL, width=210)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        logo = tk.Label(self.sidebar, text="🌾 AgroStock",
                        bg=self.BG_PANEL, fg=self.ACCENT,
                        font=("Consolas", 16, "bold"), pady=20)
        logo.pack()

        subtitle = tk.Label(self.sidebar, text="Inventory Intelligence",
                            bg=self.BG_PANEL, fg=self.TEXT_DIM,
                            font=("Consolas", 9))
        subtitle.pack()

        ttk.Separator(self.sidebar).pack(fill=tk.X, pady=12, padx=12)

        nav_items = [
            ("📊  Dashboard",    self._show_dashboard),
            ("📦  Inventory",    self._show_inventory),
            ("➕  Add Product",  self._show_add_product),
            ("🎲  Simulation",   self._show_simulation),
            ("📈  Reports",      self._show_reports),
            ("🔄  Transactions", self._show_transactions),
        ]

        self.nav_buttons = []
        for label, cmd in nav_items:
            btn = tk.Button(self.sidebar, text=label,
                            bg=self.BG_PANEL, fg=self.TEXT_MAIN,
                            activebackground=self.BTN_BG,
                            activeforeground=self.ACCENT,
                            font=("Consolas", 11), anchor="w",
                            padx=18, pady=8, bd=0, cursor="hand2",
                            command=cmd)
            btn.pack(fill=tk.X, padx=6, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.BTN_BG))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.BG_PANEL))
            self.nav_buttons.append(btn)

        # Version at bottom
        ver = tk.Label(self.sidebar, text="v1.0 | Stochastic Model",
                       bg=self.BG_PANEL, fg=self.TEXT_DIM,
                       font=("Consolas", 8))
        ver.pack(side=tk.BOTTOM, pady=12)

        # ── Main Content Area ──
        self.main = tk.Frame(self.root, bg=self.BG_DARK)
        self.main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _clear_main(self):
        for widget in self.main.winfo_children():
            widget.destroy()

    def _header(self, title, subtitle=""):
        hdr = tk.Frame(self.main, bg=self.BG_DARK)
        hdr.pack(fill=tk.X, padx=24, pady=(20, 8))
        tk.Label(hdr, text=title, bg=self.BG_DARK, fg=self.ACCENT,
                 font=("Consolas", 20, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(hdr, text=subtitle, bg=self.BG_DARK, fg=self.TEXT_DIM,
                     font=("Consolas", 10)).pack(anchor="w")
        ttk.Separator(self.main).pack(fill=tk.X, padx=24, pady=4)

    def _card(self, parent, title, value, color, icon=""):
        f = tk.Frame(parent, bg=self.BG_CARD, padx=18, pady=14,
                     relief="flat", bd=0)
        tk.Label(f, text=f"{icon} {title}", bg=self.BG_CARD,
                 fg=self.TEXT_DIM, font=("Consolas", 9)).pack(anchor="w")
        tk.Label(f, text=str(value), bg=self.BG_CARD,
                 fg=color, font=("Consolas", 22, "bold")).pack(anchor="w")
        return f

    # ── DASHBOARD ──
    def _show_dashboard(self):
        self._clear_main()
        self._header("Dashboard", "Real-time Agricultural Inventory Overview")

        rows = self.db.get_all_products()
        products = [self.db.row_to_product(r) for r in rows]

        total = len(products)
        low_stock = sum(1 for p in products if p.needs_reorder())
        expiring = sum(1 for p in products if p.is_expiring_soon())
        healthy = total - low_stock - expiring

        # Stat cards
        cards_frame = tk.Frame(self.main, bg=self.BG_DARK)
        cards_frame.pack(fill=tk.X, padx=24, pady=10)

        stats = [
            ("Total Products", total, self.ACCENT, "📦"),
            ("Healthy Stock",  healthy, "#5dbb70", "✅"),
            ("Low Stock",      low_stock, self.ACCENT2, "⚠️"),
            ("Expiring Soon",  expiring, self.ACCENT3, "🚨"),
        ]
        for title, val, color, icon in stats:
            c = self._card(cards_frame, title, val, color, icon)
            c.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=6)

        # Alerts
        alerts_frame = tk.Frame(self.main, bg=self.BG_CARD,
                                padx=16, pady=12)
        alerts_frame.pack(fill=tk.X, padx=24, pady=(10, 4))
        tk.Label(alerts_frame, text="⚡ Active Alerts",
                 bg=self.BG_CARD, fg=self.ACCENT2,
                 font=("Consolas", 12, "bold")).pack(anchor="w")

        alert_scroll = tk.Frame(alerts_frame, bg=self.BG_CARD)
        alert_scroll.pack(fill=tk.X)

        shown = 0
        for p in products:
            status = p.get_status()
            if status != "HEALTHY":
                color = self.ACCENT3 if "OUT" in status or "EXPIRING" in status else self.ACCENT2
                msg = f"  {p.name} ({p.category}) — {status}  |  Stock: {p.current_stock:.1f} {p.unit}"
                tk.Label(alert_scroll, text=msg,
                         bg=self.BG_CARD, fg=color,
                         font=("Consolas", 10)).pack(anchor="w", pady=1)
                shown += 1
        if shown == 0:
            tk.Label(alert_scroll, text="  ✅ All products are in healthy stock levels.",
                     bg=self.BG_CARD, fg="#5dbb70",
                     font=("Consolas", 10)).pack(anchor="w")

        # Quick stock table
        tk.Label(self.main, text="📋  Quick Stock View",
                 bg=self.BG_DARK, fg=self.TEXT_MAIN,
                 font=("Consolas", 12, "bold")).pack(anchor="w", padx=24, pady=(12, 4))

        cols = ("Product", "Category", "Stock", "Reorder Pt", "Shelf Life", "Status")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=10)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")

        for p in products:
            status = p.get_status()
            tag = "low" if "LOW" in status else ("critical" if "OUT" in status or "EXPIRING" in status else "ok")
            tree.insert("", tk.END,
                        values=(p.name, p.category,
                                f"{p.current_stock:.1f} {p.unit}",
                                f"{p.reorder_point:.1f} {p.unit}",
                                f"{p.shelf_life_days} days",
                                status),
                        tags=(tag,))

        tree.tag_configure("ok",       background="#253020")
        tree.tag_configure("low",      background="#3d3000")
        tree.tag_configure("critical", background="#3d1a00")

        scrollbar = ttk.Scrollbar(self.main, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 16))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # ── INVENTORY ──
    def _show_inventory(self):
        self._clear_main()
        self._header("Inventory Management", "View, Update, and Delete Products")

        btn_row = tk.Frame(self.main, bg=self.BG_DARK)
        btn_row.pack(fill=tk.X, padx=24, pady=(6, 6))

        def refresh():
            for item in tree.get_children():
                tree.delete(item)
            for row in self.db.get_all_products():
                p = self.db.row_to_product(row)
                status = p.get_status()
                tag = "low" if "LOW" in status else ("critical" if "OUT" in status or "EXPIRING" in status else "ok")
                tree.insert("", tk.END,
                            values=(row[0], p.name, p.category,
                                    f"{p.current_stock:.1f}", p.unit,
                                    p.reorder_point, p.shelf_life_days,
                                    f"{p.spoilage_rate*100:.1f}%",
                                    f"₹{p.unit_cost:.2f}", status),
                            tags=(tag,))

        def restock_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select Product", "Please select a product first.")
                return
            pid = tree.item(sel[0])["values"][0]
            pname = tree.item(sel[0])["values"][1]
            cur = float(tree.item(sel[0])["values"][3])

            win = tk.Toplevel(self.root)
            win.title(f"Restock: {pname}")
            win.configure(bg=self.BG_DARK)
            win.geometry("300x180")
            tk.Label(win, text=f"Add stock for: {pname}",
                     bg=self.BG_DARK, fg=self.ACCENT,
                     font=("Consolas", 11, "bold")).pack(pady=10)
            tk.Label(win, text=f"Current Stock: {cur}",
                     bg=self.BG_DARK, fg=self.TEXT_DIM,
                     font=("Consolas", 10)).pack()
            tk.Label(win, text="Quantity to Add:",
                     bg=self.BG_DARK, fg=self.TEXT_MAIN,
                     font=("Consolas", 10)).pack(pady=(10, 2))
            qty_var = tk.StringVar()
            tk.Entry(win, textvariable=qty_var, bg=self.BG_CARD,
                     fg=self.TEXT_MAIN, insertbackground=self.TEXT_MAIN,
                     font=("Consolas", 11), width=14).pack()

            def do_restock():
                try:
                    qty = float(qty_var.get())
                    self.db.update_stock(pid, cur + qty)
                    self.db.log_transaction(pid, pname, "RESTOCK", qty)
                    refresh()
                    win.destroy()
                    messagebox.showinfo("Success", f"Restocked {qty} units of {pname}!")
                except ValueError:
                    messagebox.showerror("Error", "Enter a valid number.")

            tk.Button(win, text="✅ Confirm Restock",
                      bg=self.BTN_BG, fg=self.TEXT_MAIN,
                      font=("Consolas", 10), command=do_restock,
                      padx=10, pady=6, bd=0, cursor="hand2").pack(pady=12)

        def delete_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select Product", "Please select a product first.")
                return
            pid = tree.item(sel[0])["values"][0]
            pname = tree.item(sel[0])["values"][1]
            if messagebox.askyesno("Delete", f"Delete {pname}?"):
                self.db.delete_product(pid)
                refresh()

        for label, cmd, color in [
            ("🔄 Refresh", refresh, self.BTN_BG),
            ("📦 Restock Selected", restock_selected, "#3d5c2a"),
            ("🗑️ Delete Selected", delete_selected, "#5c2a2a"),
        ]:
            tk.Button(btn_row, text=label, bg=color, fg=self.TEXT_MAIN,
                      font=("Consolas", 10), command=cmd,
                      padx=12, pady=6, bd=0, cursor="hand2").pack(side=tk.LEFT, padx=4)

        cols = ("ID", "Product", "Category", "Stock", "Unit",
                "Reorder Pt", "Shelf Life", "Spoilage Rate", "Unit Cost", "Status")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=18)
        widths = [40, 120, 100, 80, 50, 90, 80, 100, 90, 110]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        tree.tag_configure("ok",       background="#253020")
        tree.tag_configure("low",      background="#3d3000")
        tree.tag_configure("critical", background="#3d1a00")

        sb = ttk.Scrollbar(self.main, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        refresh()

    # ── ADD PRODUCT ──
    def _show_add_product(self):
        self._clear_main()
        self._header("Add New Product", "Register a new agricultural product")

        form = tk.Frame(self.main, bg=self.BG_CARD, padx=30, pady=24)
        form.pack(padx=40, pady=16, fill=tk.X)

        fields = [
            ("Product Name",       "Tomatoes",    "name"),
            ("Category",           "Vegetable",   "category"),
            ("Shelf Life (days)",  "7",            "shelf_life"),
            ("Current Stock (kg)", "150",          "stock"),
            ("Reorder Point (kg)", "50",           "reorder"),
            ("Unit Cost (₹/kg)",   "18.00",        "cost"),
            ("Spoilage Rate (0-1)","0.10",          "spoilage"),
            ("Unit",               "kg",           "unit"),
        ]

        self.form_vars = {}
        for i, (label, default, key) in enumerate(fields):
            row = tk.Frame(form, bg=self.BG_CARD)
            row.pack(fill=tk.X, pady=6)
            tk.Label(row, text=label, bg=self.BG_CARD, fg=self.TEXT_DIM,
                     font=("Consolas", 10), width=22, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=default)
            self.form_vars[key] = var
            tk.Entry(row, textvariable=var, bg=self.BG_DARK, fg=self.TEXT_MAIN,
                     insertbackground=self.TEXT_MAIN,
                     font=("Consolas", 11), width=24,
                     relief="flat", bd=4).pack(side=tk.LEFT, padx=8)

        def submit():
            try:
                self.db.add_product(
                    name=self.form_vars["name"].get(),
                    category=self.form_vars["category"].get(),
                    shelf_life=int(self.form_vars["shelf_life"].get()),
                    stock=float(self.form_vars["stock"].get()),
                    reorder=float(self.form_vars["reorder"].get()),
                    cost=float(self.form_vars["cost"].get()),
                    spoilage=float(self.form_vars["spoilage"].get()),
                    unit=self.form_vars["unit"].get()
                )
                messagebox.showinfo("Success",
                    f"✅ Product '{self.form_vars['name'].get()}' added successfully!")
                self._show_add_product()
            except ValueError as e:
                messagebox.showerror("Input Error", f"Please check your inputs.\n{e}")

        tk.Button(form, text="✅  Add Product",
                  bg=self.ACCENT, fg=self.BG_DARK,
                  font=("Consolas", 12, "bold"),
                  command=submit, padx=20, pady=10, bd=0,
                  cursor="hand2").pack(pady=16)

    # ── SIMULATION ──
    def _show_simulation(self):
        self._clear_main()
        self._header("Monte Carlo Simulation",
                     "Stochastic demand & spoilage analysis over time")

        rows = self.db.get_all_products()
        if not rows:
            tk.Label(self.main, text="No products found.",
                     bg=self.BG_DARK, fg=self.TEXT_DIM).pack(pady=40)
            return

        # Controls
        ctrl = tk.Frame(self.main, bg=self.BG_CARD, padx=20, pady=14)
        ctrl.pack(fill=tk.X, padx=24, pady=8)

        names = [r[1] for r in rows]
        product_var = tk.StringVar(value=names[0])
        sims_var    = tk.StringVar(value="300")
        days_var    = tk.StringVar(value="30")
        demand_var  = tk.StringVar(value="15")
        dist_var    = tk.StringVar(value="normal")

        params = [
            ("Select Product:",     product_var, names,     True),
            ("Num Simulations:",    sims_var,    None,      False),
            ("Time Horizon (days):", days_var,   None,      False),
            ("Mean Daily Demand:",  demand_var,  None,      False),
            ("Distribution:",       dist_var,    ["normal","poisson"], True),
        ]

        for label, var, options, is_combo in params:
            f = tk.Frame(ctrl, bg=self.BG_CARD)
            f.pack(side=tk.LEFT, padx=14)
            tk.Label(f, text=label, bg=self.BG_CARD, fg=self.TEXT_DIM,
                     font=("Consolas", 9)).pack(anchor="w")
            if is_combo:
                cb = ttk.Combobox(f, textvariable=var, values=options,
                                  width=16, state="readonly",
                                  font=("Consolas", 10))
                cb.pack()
            else:
                tk.Entry(f, textvariable=var, bg=self.BG_DARK,
                         fg=self.TEXT_MAIN, insertbackground=self.TEXT_MAIN,
                         font=("Consolas", 11), width=8,
                         relief="flat", bd=3).pack()

        # Progress bar
        progress_var = tk.IntVar()
        progress_bar = ttk.Progressbar(self.main, variable=progress_var,
                                       maximum=100, mode="determinate",
                                       style="TProgressbar")
        progress_bar.pack(fill=tk.X, padx=24, pady=(4, 0))

        # Results frame
        result_frame = tk.Frame(self.main, bg=self.BG_DARK)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)

        def run_sim():
            name = product_var.get()
            row = next(r for r in rows if r[1] == name)
            product = self.db.row_to_product(row)

            try:
                n_sims = int(sims_var.get())
                horizon = int(days_var.get())
                mean_d  = float(demand_var.get())
            except ValueError:
                messagebox.showerror("Error", "Enter valid numeric parameters.")
                return

            demand_model = StochasticDemandModel(
                mean_demand=mean_d,
                std_demand=mean_d * 0.3,
                distribution=dist_var.get()
            )
            simulator = MonteCarloSimulator(product, demand_model,
                                            n_sims, horizon)

            for w in result_frame.winfo_children():
                w.destroy()
            progress_var.set(0)

            def run():
                summary = simulator.run(
                    progress_callback=lambda v: progress_var.set(v)
                )
                self.root.after(0, lambda: show_results(summary, simulator))

            threading.Thread(target=run, daemon=True).start()

        def show_results(summary, simulator):
            for w in result_frame.winfo_children():
                w.destroy()

            # Stat cards
            cards = tk.Frame(result_frame, bg=self.BG_DARK)
            cards.pack(fill=tk.X, pady=6)

            sim_stats = [
                ("Avg Final Stock", f"{summary['avg_final_stock']:.1f}", self.ACCENT),
                ("Stockout Risk",   f"{summary['stockout_probability']:.1f}%", self.ACCENT3),
                ("Service Level",   f"{summary['service_level']:.1f}%", "#5dbb70"),
                ("Avg Spoilage",    f"{summary['avg_spoilage']:.1f} kg", self.ACCENT2),
                ("Simulations",     str(summary['simulations_run']), self.TEXT_DIM),
            ]
            for title, val, color in sim_stats:
                c = self._card(cards, title, val, color)
                c.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=4)

            # Chart
            paths = simulator.get_percentile_paths()
            fig = Figure(figsize=(10, 4), facecolor=self.BG_CARD)
            ax = fig.add_subplot(111)
            ax.set_facecolor(self.BG_CARD)
            ax.tick_params(colors=self.TEXT_DIM)
            for spine in ax.spines.values():
                spine.set_edgecolor(self.TEXT_DIM)

            days_range = paths["days"]
            ax.fill_between(days_range, paths["p10"], paths["p90"],
                            alpha=0.25, color=self.ACCENT, label="10th–90th Percentile")
            ax.plot(days_range, paths["p50"], color=self.ACCENT,
                    linewidth=2.5, label="Median (P50)")
            ax.plot(days_range, paths["p10"], color=self.ACCENT2,
                    linewidth=1, linestyle="--", label="P10 (Pessimistic)")
            ax.plot(days_range, paths["p90"], color="#5dbb70",
                    linewidth=1, linestyle="--", label="P90 (Optimistic)")

            rp = simulator.product.reorder_point
            ax.axhline(y=rp, color=self.ACCENT3, linewidth=1.5,
                       linestyle=":", label=f"Reorder Point ({rp:.0f})")

            ax.set_xlabel("Days", color=self.TEXT_DIM)
            ax.set_ylabel("Stock Level (kg)", color=self.TEXT_DIM)
            ax.set_title(f"Monte Carlo Stock Simulation — {simulator.product.name}",
                         color=self.TEXT_MAIN, fontsize=12, fontweight="bold")
            ax.legend(facecolor=self.BG_PANEL, edgecolor=self.TEXT_DIM,
                      labelcolor=self.TEXT_MAIN, fontsize=8)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=result_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        tk.Button(ctrl, text="▶  Run Simulation",
                  bg=self.ACCENT, fg=self.BG_DARK,
                  font=("Consolas", 11, "bold"),
                  command=run_sim, padx=14, pady=8, bd=0,
                  cursor="hand2").pack(side=tk.LEFT, padx=20, pady=4, anchor="s")

    # ── REPORTS ──
    def _show_reports(self):
        self._clear_main()
        self._header("Reports & Analytics", "Visual analysis of inventory data")

        rows = self.db.get_all_products()
        products = [self.db.row_to_product(r) for r in rows]

        fig = Figure(figsize=(11, 7), facecolor=self.BG_DARK)
        fig.patch.set_facecolor(self.BG_DARK)

        axes = [fig.add_subplot(2, 3, i+1) for i in range(5)]
        for ax in axes:
            ax.set_facecolor(self.BG_CARD)
            ax.tick_params(colors=self.TEXT_DIM, labelsize=7)
            for spine in ax.spines.values():
                spine.set_edgecolor(self.TEXT_DIM)

        names = [p.name for p in products]
        stocks = [p.current_stock for p in products]
        colors = [self.ACCENT if not p.needs_reorder() else self.ACCENT2
                  if not p.is_expiring_soon() else self.ACCENT3
                  for p in products]

        # 1. Stock bar chart
        axes[0].barh(names, stocks, color=colors)
        axes[0].set_title("Current Stock Levels", color=self.TEXT_MAIN, fontsize=9)
        axes[0].set_xlabel("Stock (kg)", color=self.TEXT_DIM, fontsize=7)
        axes[0].tick_params(axis='y', labelsize=6)

        # 2. Category pie
        from collections import Counter
        cats = Counter(p.category for p in products)
        pie_colors = [self.ACCENT, self.ACCENT2, self.ACCENT3, "#5dbb70",
                      "#5588cc", "#cc55aa", "#aa8855"]
        axes[1].pie(cats.values(), labels=cats.keys(),
                    colors=pie_colors[:len(cats)], autopct="%1.0f%%",
                    textprops={"color": self.TEXT_MAIN, "fontsize": 7})
        axes[1].set_title("Products by Category", color=self.TEXT_MAIN, fontsize=9)

        # 3. Spoilage rates
        spoilage = [p.spoilage_rate * 100 for p in products]
        axes[2].bar(range(len(names)), spoilage, color=self.ACCENT3)
        axes[2].set_xticks(range(len(names)))
        axes[2].set_xticklabels(names, rotation=45, ha="right", fontsize=5)
        axes[2].set_title("Spoilage Rates (%)", color=self.TEXT_MAIN, fontsize=9)
        axes[2].set_ylabel("%", color=self.TEXT_DIM, fontsize=7)

        # 4. Stock vs Reorder Point
        reorders = [p.reorder_point for p in products]
        x = range(len(names))
        axes[3].bar([i - 0.2 for i in x], stocks, 0.4,
                    label="Current", color=self.ACCENT)
        axes[3].bar([i + 0.2 for i in x], reorders, 0.4,
                    label="Reorder Pt", color=self.ACCENT2)
        axes[3].set_xticks(list(x))
        axes[3].set_xticklabels(names, rotation=45, ha="right", fontsize=5)
        axes[3].legend(facecolor=self.BG_PANEL, labelcolor=self.TEXT_MAIN,
                       fontsize=6, edgecolor=self.TEXT_DIM)
        axes[3].set_title("Stock vs Reorder Point", color=self.TEXT_MAIN, fontsize=9)

        # 5. Monte Carlo demand distribution (sample)
        if products:
            p = products[0]
            model = StochasticDemandModel(15, 4.5)
            sim_demands = model.simulate_demand(1000)
            axes[4].hist(sim_demands, bins=30, color=self.ACCENT,
                         edgecolor=self.BG_DARK, alpha=0.85)
            axes[4].set_title(f"Simulated Daily Demand\n(Normal Dist, μ=15, σ=4.5)",
                              color=self.TEXT_MAIN, fontsize=8)
            axes[4].set_xlabel("Demand (kg)", color=self.TEXT_DIM, fontsize=7)
            axes[4].set_ylabel("Frequency", color=self.TEXT_DIM, fontsize=7)

        fig.tight_layout(pad=2.0)
        canvas = FigureCanvasTkAgg(fig, master=self.main)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

    # ── TRANSACTIONS ──
    def _show_transactions(self):
        self._clear_main()
        self._header("Transaction History", "All stock movements and restock events")

        cols = ("ID", "Product", "Type", "Quantity", "Date", "Notes")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=22)
        widths = [50, 160, 110, 100, 200, 200]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        for row in self.db.get_transactions(100):
            color_tag = "restock" if row[3] == "RESTOCK" else "consume"
            tree.insert("", tk.END,
                        values=(row[0], row[2], row[3],
                                f"{row[4]:.1f}", row[5], row[6] or "—"),
                        tags=(color_tag,))

        tree.tag_configure("restock", background="#1a2d1a")
        tree.tag_configure("consume", background="#2d1a1a")

        sb = ttk.Scrollbar(self.main, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        if not self.db.get_transactions(1):
            tk.Label(self.main,
                     text="No transactions yet. Restock products to log activity.",
                     bg=self.BG_DARK, fg=self.TEXT_DIM,
                     font=("Consolas", 11)).pack(pady=30)

    def run(self):
        self.root.mainloop()


# ─────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = InventoryGUI()
    app.run()
