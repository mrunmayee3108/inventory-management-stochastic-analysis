import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

from product import PerishableProduct
from inventory import Inventory
from stochastic import MonteCarloSimulator

C = {
    "bg":     "#F8FAF5",  "sidebar": "#1C3A2A",  "hover":  "#2A5240",
    "card":   "#FFFFFF",  "border":  "#E0E8E2",   "text":   "#1A2E22",
    "muted":  "#6B8F71",  "green":   "#2D6A4F",   "red":    "#C0392B",
    "amber":  "#D4890A",  "blue":    "#2471A3",    "teal":   "#27AE60",
    "purple": "#7D3C98",
    "red_bg": "#FDEDEC",  "amb_bg":  "#FEF9E7",   "grn_bg": "#EAFAF1",
    "blu_bg": "#EBF5FB",
}

class InventoryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AgriStock — Stochastic Perishable Inventory System")
        self.root.geometry("1280x760")
        self.root.configure(bg=C["bg"])
        self.root.minsize(1050, 640)

        self.inv = Inventory()  
        self.last_mc_profits = []            

        self._build_window()
        self._start_clock()
        self.show_dashboard()

    def _build_window(self):
        self._build_topbar()
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True)
        self._build_sidebar(body)
        self.content = tk.Frame(body, bg=C["bg"])
        self.content.pack(side="left", fill="both", expand=True)

    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=C["sidebar"], height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="🌿 AgriStock",
                 bg=C["sidebar"], fg="white",
                 font=("Segoe UI",15,"bold")).pack(side="left", padx=18)
        tk.Label(bar, text="Stochastic Perishable Inventory System",
                 bg=C["sidebar"], fg="#A8C9B0",
                 font=("Segoe UI",10)).pack(side="left")
        self.clock_lbl = tk.Label(bar, bg=C["sidebar"], fg="#A8C9B0",
                                   font=("Segoe UI",10))
        self.clock_lbl.pack(side="right", padx=18)
        self.alert_lbl = tk.Label(bar, text="",
                 bg=C["red"], fg="white",
                 font=("Segoe UI",9,"bold"))
        self.alert_lbl.pack(side="right", padx=6, pady=12)

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=C["sidebar"], width=200)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        tk.Frame(sb, bg=C["sidebar"], height=14).pack()
        self.nav_btns = {}
        for label, cmd in [
            ("📊  Dashboard", self.show_dashboard),
            ("📦  Manage Products", self.show_manage),
            ("🎲  Simulation", self.show_simulation),
            ("📈  Reports", self.show_reports),
            ("🗑️  Spoilage", self.show_spoilage),
        ]:
            b = tk.Button(sb, text=label,
                          bg=C["sidebar"], fg="white",
                          font=("Segoe UI",10), relief="flat",
                          anchor="w", padx=16, pady=11, cursor="hand2",
                          activebackground=C["hover"], activeforeground="white",
                          command=lambda c=cmd, l=label: self._nav(l, c))
            b.pack(fill="x")
            self.nav_btns[label] = b
        tk.Frame(sb, bg=C["sidebar"]).pack(fill="y", expand=True)
        wf = tk.Frame(sb, bg="#142B1E", padx=12, pady=10)
        wf.pack(fill="x")
        tk.Label(wf, text="☀  Today's Weather",
                 bg="#142B1E", fg="#A8C9B0",
                 font=("Segoe UI",8,"bold")).pack(anchor="w")
        tk.Label(wf, text="34°C  ·  Clear  ·  Good harvest expected",
                 bg="#142B1E", fg="#6B9E75",
                 font=("Segoe UI",8), wraplength=170).pack(anchor="w", pady=(3,0))

    def _nav(self, label, cmd):
        for l, b in self.nav_btns.items():
            b.config(bg=C["hover"] if l == label else C["sidebar"])
        cmd()

    def _refresh_alert(self):
        n = len(self.inv.low_stock())
        self.alert_lbl.config(text=f"  {n} low-stock alerts  ")

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _start_clock(self):
        def tick():
            self.clock_lbl.config(text=time.strftime("  %a %d %b   %H:%M:%S  "))
            self.root.after(1000, tick)
        tick()

    def _card(self, parent, **kw):
        return tk.Frame(parent, bg=C["card"],
                        highlightthickness=1,
                        highlightbackground=C["border"], **kw)

    def _btn(self, parent, text, bg, cmd, fg="white"):
        return tk.Button(parent, text=text, bg=bg, fg=fg,
                         font=("Segoe UI",9,"bold"), relief="flat",
                         cursor="hand2", pady=7, command=cmd)

    def _section(self, parent, text):
        tk.Label(parent, text=text, bg=C["card"], fg=C["text"],
                 font=("Segoe UI",11,"bold")).pack(
                     anchor="w", padx=14, pady=(12,6))

    def _scrollable(self, parent):
        cv = tk.Canvas(parent, bg=C["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(cv, bg=C["bg"])
        wid = cv.create_window((0,0), window=inner, anchor="nw")
        cv.bind("<Configure>", lambda e: cv.itemconfig(wid, width=e.width))
        inner.bind("<Configure>",
                   lambda e: cv.configure(scrollregion=cv.bbox("all")))
        return inner

    def _table_hdr(self, parent, cols, widths):
        hdr = tk.Frame(parent, bg="#EFF4F0")
        hdr.pack(fill="x", padx=14)
        for col, w in zip(cols, widths):
            tk.Label(hdr, text=col, bg="#EFF4F0", fg=C["muted"],
                     font=("Segoe UI",8,"bold"), width=w,
                     anchor="w").pack(side="left", padx=4, pady=4)

    def _kpi(self, frame, i, label, value, colour, sub):
        frame.columnconfigure(i, weight=1)
        c = self._card(frame)
        c.grid(row=0, column=i, padx=4, sticky="ew")
        tk.Label(c, text=label, bg=C["card"], fg=C["muted"],
                 font=("Segoe UI",9)).pack(anchor="w", padx=12, pady=(10,0))
        tk.Label(c, text=value, bg=C["card"], fg=colour,
                 font=("Segoe UI",22,"bold")).pack(anchor="w", padx=12)
        tk.Label(c, text=sub, bg=C["card"], fg=C["muted"],
                 font=("Segoe UI",8)).pack(anchor="w", padx=12, pady=(0,10))

    def show_dashboard(self):
        self._clear()
        self._refresh_alert()
        page = self._scrollable(self.content)
        tk.Label(page, text="Dashboard",
                 bg=C["bg"], fg=C["text"],
                 font=("Segoe UI",20,"bold")).pack(
                     anchor="w", padx=20, pady=(14,8))

        inv = self.inv
        low = inv.low_stock()
        expiring = inv.expiring_soon()
        total = sum(p.current_stock for p in inv.products)

        kf = tk.Frame(page, bg=C["bg"])
        kf.pack(fill="x", padx=20, pady=(0,10))
        self._kpi(kf, 0, "Total Stock", f"{total:.0f} units", C["green"], "All products")
        self._kpi(kf, 1, "Low Stock", str(len(low)), C["red"], "Need reorder")
        self._kpi(kf, 2, "Expiring Soon", str(len(expiring)), C["amber"], "Within 3 days")
        self._kpi(kf, 3, "Products", str(len(inv.products)),C["blue"], "In warehouse")

        mid = tk.Frame(page, bg=C["bg"])
        mid.pack(fill="x", padx=20, pady=(0,10))
        mid.columnconfigure(0, weight=3); mid.columnconfigure(1, weight=2)

        cc = self._card(mid)
        cc.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        self._section(cc, "Stock Levels by Product")
        names = [p.name for p in inv.products]
        stocks = [p.current_stock for p in inv.products]
        rps = [p.reorder_point for p in inv.products]
        cols = [C["red"] if s < r else C["green"] for s,r in zip(stocks,rps)]
        fig, ax = plt.subplots(figsize=(6,3.4))
        fig.patch.set_facecolor("white"); ax.set_facecolor("#f9fafb")
        ax.barh(names, stocks, color=cols, height=0.55)
        for rp in rps:
            ax.axvline(x=rp, color=C["amber"], linewidth=1.2,
                       linestyle="--", alpha=0.7)
        ax.set_xlabel("Units", fontsize=9); ax.tick_params(labelsize=9)
        ax.set_title("Green = OK  |  Red = Below Reorder  |  Dashed = Reorder Point",
                     fontsize=8, color=C["muted"])
        fig.tight_layout()
        FigureCanvasTkAgg(fig, cc).get_tk_widget().pack(
            fill="both", expand=True, padx=8, pady=(0,8))
        plt.close(fig)

        ac = self._card(mid)
        ac.grid(row=0, column=1, sticky="nsew")
        self._section(ac, "🔔  Alerts")
        if not low and not expiring:
            tk.Label(ac, text="✅  All levels are healthy.",
                     bg=C["card"], fg=C["teal"],
                     font=("Segoe UI",9)).pack(padx=12, pady=6, anchor="w")
        for p in low:
            f = tk.Frame(ac, bg=C["red_bg"]); f.pack(fill="x", padx=10, pady=2)
            tk.Label(f, text=f"⚠️  {p.name}: {p.current_stock:.0f} {p.unit} left",
                     bg=C["red_bg"], fg=C["red"], font=("Segoe UI",9),
                     wraplength=240).pack(anchor="w", padx=8, pady=4)
        for p in expiring:
            f = tk.Frame(ac, bg=C["amb_bg"]); f.pack(fill="x", padx=10, pady=2)
            tk.Label(f, text=f"⏰  {p.name}: {p.days_left()} day(s) left",
                     bg=C["amb_bg"], fg=C["amber"], font=("Segoe UI",9),
                     wraplength=240).pack(anchor="w", padx=8, pady=4)

        tc = self._card(page)
        tc.pack(fill="x", padx=20, pady=(0,20))
        self._section(tc, "Recent Activity")
        self._table_hdr(tc, ["Time","Product","Action","Qty","Note"],
                        [14,14,10,6,26])
        col_map = {"DELIVERY":C["teal"],"SALE":C["blue"],
                   "SPOILED":C["red"],"ADDED":C["green"],"DELETED":C["red"]}
        for tx in inv.recent_log(12):
            row = tk.Frame(tc, bg=C["card"]); row.pack(fill="x", padx=14, pady=1)
            for val, w, fg in [
                (tx["time"],    14, C["muted"]),
                (tx["product"], 14, C["text"]),
                (tx["action"],  10, col_map.get(tx["action"], C["muted"])),
                (str(tx["qty"]), 6, C["text"]),
                (tx["note"],    26, C["muted"]),
            ]:
                tk.Label(row, text=val, bg=C["card"], fg=fg,
                         font=("Segoe UI",9), width=w,
                         anchor="w").pack(side="left", padx=4, pady=3)

    def show_manage(self):
        self._clear()
        self._refresh_alert()
        page = self._scrollable(self.content)
        tk.Label(page, text="Manage Products",
                 bg=C["bg"], fg=C["text"],
                 font=("Segoe UI",20,"bold")).pack(
                     anchor="w", padx=20, pady=(14,8))

        top = tk.Frame(page, bg=C["bg"])
        top.pack(fill="x", padx=20, pady=(0,14))
        top.columnconfigure(0, weight=1); top.columnconfigure(1, weight=1)

        add_card = self._card(top)
        add_card.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        self._section(add_card, "Add a New Product")

        field_defs = [
            ("Product Name", "", "e.g.  Carrots, Paneer, Apples"),
            ("Category", "Vegetable", "Vegetable / Fruit / Dairy / Bakery"),
            ("Unit", "kg", "kg  /  litres  /  pcs"),
            ("Current Stock", "0", "How many units do you have right now?"),
            ("Reorder Point", "20", "Reorder when stock falls below this number"),
            ("Reorder Quantity", "50", "How many units to order each time"),
            ("Shelf Life (days)","5", "How many days before it expires"),
            ("Sale Price (₹)", "", "Price you sell one unit for"),
            ("Avg Daily Demand", "", "Roughly how many units you sell per day"),
        ]
        entries = {}
        for label, default, hint in field_defs:
            row = tk.Frame(add_card, bg=C["card"])
            row.pack(fill="x", padx=14, pady=3)
            tk.Label(row, text=label, bg=C["card"], fg=C["text"],
                     font=("Segoe UI",9,"bold"), width=18,
                     anchor="w").pack(side="left")
            e = tk.Entry(row, bg="#F8FAF5", fg=C["text"],
                         font=("Segoe UI",9), width=12,
                         relief="solid", bd=1)
            e.insert(0, default)
            e.pack(side="left", padx=6)
            tk.Label(row, text=hint, bg=C["card"], fg=C["muted"],
                     font=("Segoe UI",8)).pack(side="left", padx=2)
            entries[label] = e

        info = tk.Frame(add_card, bg=C["blu_bg"])
        info.pack(fill="x", padx=14, pady=(6,0))
        tk.Label(info,
                 text="ℹ️  The following are automatically calculated for you:\n"
                      "    • Waste cost = 30% of sale price\n"
                      "    • Stockout penalty = 60% of sale price\n"
                      "    • Demand variation = 20% of avg demand",
                 bg=C["blu_bg"], fg=C["blue"],
                 font=("Segoe UI",8), justify="left").pack(
                     anchor="w", padx=8, pady=6)

        def do_add():
            name = entries["Product Name"].get().strip()
            if not name:
                messagebox.showwarning("Missing", "Please enter a product name.")
                return
            if self.inv.get(name):
                messagebox.showwarning("Exists", f"'{name}' already exists.")
                return
            try:
                p = PerishableProduct(
                    name = name,
                    category = entries["Category"].get(),
                    unit = entries["Unit"].get(),
                    stock = float(entries["Current Stock"].get()),
                    reorder_point = int(entries["Reorder Point"].get()),
                    reorder_qty = int(entries["Reorder Quantity"].get()),
                    shelf_life = int(entries["Shelf Life (days)"].get()),
                    sale_price = float(entries["Sale Price (₹)"].get()),
                    avg_demand = float(entries["Avg Daily Demand"].get()),
                )
                self.inv.add_product(p)
                messagebox.showinfo(
                    "✅ Product Added",
                    f"'{name}' added to inventory!\n\n"
                    f"Auto-calculated values:\n"
                    f"Waste cost = ₹{p.waste_cost} per unit\n"
                    f"Stockout cost = ₹{p.stockout_cost} per unit\n"
                    f"Critical Ratio = {p.critical_ratio()}")
                self.show_manage()
            except ValueError as ex:
                messagebox.showerror("Invalid Input", f"Please check your numbers.\n\n{ex}")

        self._btn(add_card, "➕  Add Product",
                  C["green"], do_add).pack(fill="x", padx=14, pady=10)

        qa = self._card(top)
        qa.grid(row=0, column=1, sticky="nsew")
        self._section(qa, "Record Delivery / Sale")

        tk.Label(qa, text="Select Product", bg=C["card"], fg=C["muted"],
                 font=("Segoe UI",9)).pack(anchor="w", padx=14)
        prod_names = [p.name for p in self.inv.products]
        sel = tk.StringVar(value=prod_names[0] if prod_names else "")
        ttk.Combobox(qa, textvariable=sel, values=prod_names,
                     state="readonly", font=("Segoe UI",9), width=22
                     ).pack(padx=14, pady=(0,8), fill="x")

        tk.Label(qa, text="Quantity", bg=C["card"], fg=C["muted"],
                 font=("Segoe UI",9)).pack(anchor="w", padx=14)
        qty_var = tk.StringVar(value="0")
        tk.Entry(qa, textvariable=qty_var, bg="#F8FAF5",
                 fg=C["text"], font=("Segoe UI",9),
                 relief="solid", bd=1, width=12
                 ).pack(anchor="w", padx=14, pady=(0,12))

        def do_delivery():
            try:
                self.inv.add_stock(sel.get(), float(qty_var.get()))
                messagebox.showinfo("✅ Done", "Delivery recorded.")
                self.show_dashboard()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        def do_sale():
            try:
                sold = self.inv.sell_stock(sel.get(), float(qty_var.get()))
                messagebox.showinfo("✅ Done", f"{sold} units sold and recorded.")
                self.show_dashboard()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        def do_spoilage():
            expired = self.inv.advance_day()
            if expired:
                msg = "\n".join(f"  • {n}: {q:.0f} {u}" for n,q,u in expired)
                messagebox.showwarning("Spoilage!", f"Expired and removed:\n{msg}")
            else:
                messagebox.showinfo("All Good", "Nothing expired today.")
            self.show_dashboard()

        for txt, bg, cmd in [
            ("📦  Record Delivery",    C["teal"],  do_delivery),
            ("🛒  Record Sale",        C["blue"],  do_sale),
            ("🗑️  Run Spoilage Check", C["amber"], do_spoilage),
        ]:
            self._btn(qa, txt, bg, cmd).pack(fill="x", padx=14, pady=3)

        lc = self._card(page)
        lc.pack(fill="x", padx=20, pady=(0,20))
        self._section(lc, "All Products")
        self._table_hdr(lc,
            ["Product","Category","Stock","Reorder At",
             "Shelf Life","Expires In","Critical Ratio",""],
            [14, 12, 10, 12, 12, 12, 14, 8])

        for p in self.inv.products:
            dl  = p.days_left()
            low = p.needs_reorder()
            rbg = C["red_bg"] if low else C["card"]
            exp_col = (C["red"]   if dl <= 2
                       else C["amber"] if dl <= 4
                       else C["teal"])

            row = tk.Frame(lc, bg=rbg, highlightthickness=1,
                           highlightbackground=C["border"])
            row.pack(fill="x", padx=14, pady=1)

            for val, w, col in [
                (p.name,                 14, C["text"]),
                (p.category,             12, C["muted"]),
                (f"{p.current_stock:.0f} {p.unit}", 10,
                 C["red"] if low else C["text"]),
                (str(p.reorder_point),   12, C["muted"]),
                (f"{p.shelf_life}d",     12, C["muted"]),
                (f"{dl}d",               12, exp_col),
                (f"CR = {p.critical_ratio()}", 14, C["purple"]),
            ]:
                tk.Label(row, text=val, bg=rbg, fg=col,
                         font=("Segoe UI",9), width=w,
                         anchor="w").pack(side="left", padx=4, pady=6)
                
            def make_del(name=p.name):
                def _del():
                    if messagebox.askyesno(
                        "Confirm Delete",
                        f"Are you sure you want to delete '{name}'?\n"
                        f"This cannot be undone."
                    ):
                        self.inv.delete_product(name)
                        messagebox.showinfo("Deleted", f"'{name}' removed.")
                        self.show_manage()
                return _del

            tk.Button(row, text="🗑 Delete",
                      bg=C["red_bg"], fg=C["red"],
                      font=("Segoe UI",8,"bold"), relief="flat",
                      cursor="hand2", padx=6, pady=2,
                      command=make_del()
                      ).pack(side="left", padx=6)

    def show_simulation(self):
        self._clear()
        self._refresh_alert()
        self.content.columnconfigure(1, weight=1)
        self.content.rowconfigure(0, weight=1)

        left = self._card(self.content)
        left.grid(row=0, column=0, sticky="nsew", padx=(10,5), pady=10)
        left.config(width=265); left.pack_propagate(False)

        def sec(txt):
            f = tk.Frame(left, bg=C["card"])
            f.pack(fill="x", padx=12, pady=(12,3))
            tk.Label(f, text=txt, bg=C["card"], fg=C["text"],
                     font=("Segoe UI",8,"bold")).pack(side="left")
            tk.Frame(f, bg=C["border"], height=1).pack(
                side="left", fill="x", expand=True, padx=6)

        def erow(lbl, val, hint=""):
            f = tk.Frame(left, bg=C["card"]); f.pack(fill="x", padx=12, pady=2)
            tk.Label(f, text=lbl, bg=C["card"], fg=C["text"],
                     font=("Segoe UI",9), width=22, anchor="w").pack(side="left")
            e = tk.Entry(f, bg="#F8FAF5", fg=C["text"],
                         font=("Segoe UI",9), width=7, relief="solid", bd=1)
            e.insert(0, str(val)); e.pack(side="right")
            if hint:
                tk.Label(left, text=hint, bg=C["card"], fg=C["muted"],
                         font=("Segoe UI",7), wraplength=230
                         ).pack(anchor="w", padx=12)
            return e

        sec("PRODUCT")
        prod_var = tk.StringVar(value=self.inv.products[0].name)
        ttk.Combobox(left, textvariable=prod_var,
                     values=[p.name for p in self.inv.products],
                     state="readonly", font=("Segoe UI",9), width=24
                     ).pack(padx=12, pady=(0,6), fill="x")

        sec("SETTINGS")
        e_runs = erow("Number of runs",  300,
                      "More runs = more accurate. 300 is a good balance.")
        e_days = erow("Days to simulate", 60,
                      "How many days each run covers.")

        sec("CRITICAL RATIO  (calculated for you)")
        cr_lbl = tk.Label(left,
                          text="Run the simulation to see\nthe Critical Ratio here.",
                          bg=C["card"], fg=C["purple"],
                          font=("Segoe UI",9,"bold"), justify="left")
        cr_lbl.pack(padx=12, anchor="w")

        sec("RECOMMENDED SAFETY STOCK")
        ss_lbl = tk.Label(left,
                          text="Run the simulation to see\nthe recommendation here.",
                          bg=C["card"], fg=C["blue"],
                          font=("Segoe UI",9,"bold"), justify="left")
        ss_lbl.pack(padx=12, anchor="w")

        v_status = tk.StringVar(value="Choose a product and press  ▶ Run")
        tk.Label(left, textvariable=v_status,
                 bg=C["grn_bg"], fg=C["green"],
                 font=("Segoe UI",8), wraplength=230,
                 justify="left", padx=8, pady=6
                 ).pack(fill="x", side="bottom", padx=10, pady=8)

        right = tk.Frame(self.content, bg=C["bg"])
        right.grid(row=0, column=1, sticky="nsew", padx=(0,10), pady=10)
        right.columnconfigure(0, weight=1); right.rowconfigure(1, weight=1)

        kpis = {}
        kf = tk.Frame(right, bg=C["bg"]); kf.grid(row=0, sticky="ew", pady=(0,6))
        for i, (lbl, key, col) in enumerate([
            ("Avg Profit", "avg", C["green"]),
            ("Std Deviation", "std", C["amber"]),
            ("Best Run", "best", C["teal"]),
            ("Worst Run", "worst", C["red"]),
            ("Avg Service %", "service", C["blue"]),
            ("Avg Waste %", "waste", C["purple"]),
        ]):
            kf.columnconfigure(i, weight=1)
            c = self._card(kf); c.grid(row=0, column=i, padx=2, sticky="ew")
            tk.Label(c, text=lbl, bg=C["card"], fg=C["muted"],
                     font=("Segoe UI",7,"bold")).pack(pady=(5,0))
            v = tk.StringVar(value="—"); kpis[key] = v
            tk.Label(c, textvariable=v, bg=C["card"], fg=col,
                     font=("Segoe UI",12,"bold")).pack(pady=(0,5))

        chart_area = self._card(right)
        chart_area.grid(row=1, sticky="nsew")
        tk.Label(chart_area, text="Press  ▶ Run  to see the simulation charts here.",
                 bg=C["card"], fg=C["muted"],
                 font=("Segoe UI",12)).pack(expand=True)

        def run_sim(drought=False):
            p = self.inv.get(prod_var.get())
            if not p: return
            n    = int(e_runs.get())
            days = int(e_days.get())
            v_status.set(f"⏳ Running {n} simulations…")
            self.content.update_idletasks()

            mc = MonteCarloSimulator(p, num_runs=n, days=days)
            mc.run(drought=drought)
            res = mc.summary()
            ss  = mc.safety_stock()

            cr = p.critical_ratio()
            cr_lbl.config(
                text=f"CR  =  Cu / (Cu + Co)\n"
                     f"    =  {p.stockout_cost} / ({p.stockout_cost} + {p.waste_cost})\n"
                     f"    =  {cr}\n"
                     f"→  {'Keep MORE stock' if cr > 0.5 else 'Keep LESS stock'}")

            ss_lbl.config(
                text=f"SS  =  Z × σ × √(Lead Time)\n"
                     f"    =  1.65 × {p.demand_std:.1f} × √2\n"
                     f"    =  {ss} {p.unit}  (at 95% service level)")

            kpis["avg"].set(f"₹{res['avg_profit']:,.0f}")
            kpis["std"].set(f"₹{res['std_profit']:,.0f}")
            kpis["best"].set(f"₹{res['best']:,.0f}")
            kpis["worst"].set(f"₹{res['worst']:,.0f}")
            kpis["service"].set(f"{res['avg_service']}%")
            kpis["waste"].set(f"{res['avg_waste']}%")

            self.last_mc_profits = res["profits"]

            for w in chart_area.winfo_children():
                w.destroy()

            fig, axes = plt.subplots(1, 3, figsize=(11,3.8))
            fig.patch.set_facecolor("white")
            items = [
                (axes[0], res["profits"], C["green"], "Profit Distribution", "Total Profit (₹)"),
                (axes[1], res["services"], C["blue"],  "Service Level Distribution", "Service Level (%)"),
                (axes[2], res["wastes"], C["red"],   "Waste Rate Distribution", "Waste Rate (%)"),
            ]
            for ax, data, col, title, xlabel in items:
                ax.hist(data, bins=22, color=col, edgecolor="white")
                avg_val = sum(data)/len(data)
                ax.axvline(avg_val, color=C["amber"], linestyle="--",
                           linewidth=2, label=f"avg = {avg_val:.1f}")
                ax.set_title(title, fontsize=10, fontweight="bold")
                ax.set_xlabel(xlabel, fontsize=9)
                ax.legend(fontsize=8); ax.set_facecolor("#f9fafb")

            fig.tight_layout()
            FigureCanvasTkAgg(fig, chart_area).get_tk_widget().pack(
                fill="both", expand=True, padx=6, pady=6)
            plt.close(fig)
            v_status.set(f"✅ Done!  CR = {cr}   |   Safety Stock = {ss} {p.unit}")

        sec("RUN")
        self._btn(left, "▶  Run Simulation  (normal)",
                  C["green"], lambda: run_sim(False)).pack(fill="x", padx=12, pady=3)
        self._btn(left, "🌵  Run with Drought scenario",
                  C["red"], lambda: run_sim(True)).pack(fill="x", padx=12, pady=3)

    def show_reports(self):
        self._clear()
        self._refresh_alert()
        page = self._scrollable(self.content)
        tk.Label(page, text="Reports & Charts",
                 bg=C["bg"], fg=C["text"],
                 font=("Segoe UI",20,"bold")).pack(
                     anchor="w", padx=20, pady=(14,8))

        import numpy as np
        inv = self.inv

        c1 = self._card(page); c1.pack(fill="x", padx=20, pady=(0,10))
        self._section(c1, "Avg Daily Demand  vs  Reorder Point")
        names   = [p.name for p in inv.products]
        demands = [p.avg_demand    for p in inv.products]
        reords  = [p.reorder_point for p in inv.products]
        x = np.arange(len(names)); w = 0.35
        fig1, ax1 = plt.subplots(figsize=(10,3))
        fig1.patch.set_facecolor("white"); ax1.set_facecolor("#f9fafb")
        ax1.bar(x-w/2, demands, w, label="Avg Daily Demand", color=C["green"])
        ax1.bar(x+w/2, reords,  w, label="Reorder Point",    color=C["amber"])
        ax1.set_xticks(x)
        ax1.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
        ax1.set_ylabel("Units", fontsize=9); ax1.legend(fontsize=9)
        ax1.set_title(
            "If Avg Demand is much higher than Reorder Point, you may run out before the next delivery.",
            fontsize=8, color=C["muted"])
        fig1.tight_layout()
        FigureCanvasTkAgg(fig1, c1).get_tk_widget().pack(
            fill="x", padx=8, pady=(0,8))
        plt.close(fig1)

        c2 = self._card(page); c2.pack(fill="x", padx=20, pady=(0,10))
        self._section(c2, "Critical Ratio by Product  [CR = Cu / (Cu + Co)]")
        crs    = [p.critical_ratio() for p in inv.products]
        colors = [C["green"] if c > 0.6 else C["amber"] if c > 0.4 else C["red"]
                  for c in crs]
        fig2, ax2 = plt.subplots(figsize=(10,3))
        fig2.patch.set_facecolor("white"); ax2.set_facecolor("#f9fafb")
        ax2.bar(names, crs, color=colors, edgecolor="white")
        ax2.axhline(0.5, color=C["purple"], linestyle="--",
                    linewidth=1.5, label="CR = 0.5 (balanced)")
        ax2.set_ylim(0,1); ax2.set_ylabel("Critical Ratio", fontsize=9)
        ax2.set_xticks(range(len(names)))
        ax2.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
        ax2.legend(fontsize=9)
        ax2.set_title(
            "Green = keep more stock  |  Red = reduce stock  |  0.5 line = perfectly balanced",
            fontsize=8, color=C["muted"])
        fig2.tight_layout()
        FigureCanvasTkAgg(fig2, c2).get_tk_widget().pack(
            fill="x", padx=8, pady=(0,8))
        plt.close(fig2)

        c3 = self._card(page); c3.pack(fill="x", padx=20, pady=(0,20))
        self._section(c3, "Profit Distribution — Last Simulation Run")
        if self.last_mc_profits:
            fig3, ax3 = plt.subplots(figsize=(10,3))
            fig3.patch.set_facecolor("white"); ax3.set_facecolor("#f9fafb")
            ax3.hist(self.last_mc_profits, bins=25,
                     color=C["green"], edgecolor="white")
            avg = sum(self.last_mc_profits) / len(self.last_mc_profits)
            ax3.axvline(avg, color=C["amber"], linestyle="--",
                        linewidth=2, label=f"avg = ₹{avg:,.0f}")
            ax3.set_xlabel("Total Profit (₹)", fontsize=9)
            ax3.set_ylabel("Number of simulation runs", fontsize=9)
            ax3.legend(fontsize=9)
            ax3.set_title(
                "Each bar = how many of the 300 runs achieved that profit. "
                "A wide spread = higher risk.",
                fontsize=8, color=C["muted"])
            fig3.tight_layout()
            FigureCanvasTkAgg(fig3, c3).get_tk_widget().pack(
                fill="x", padx=8, pady=(0,8))
            plt.close(fig3)
        else:
            tk.Label(c3,
                     text="Go to the Simulation page and run a simulation first.\n"
                          "The profit chart will appear here.",
                     bg=C["card"], fg=C["muted"],
                     font=("Segoe UI",10)).pack(pady=24)

    def show_spoilage(self):
        self._clear()
        self._refresh_alert()
        page = self._scrollable(self.content)
        tk.Label(page, text="Spoilage Tracker",
                 bg=C["bg"], fg=C["text"],
                 font=("Segoe UI",20,"bold")).pack(
                     anchor="w", padx=20, pady=(14,8))

        inv = self.inv
        cc = self._card(page); cc.pack(fill="x", padx=20, pady=(0,10))
        self._section(cc, "Days Remaining Before Expiry")
        names     = [p.name       for p in inv.products]
        remaining = [p.days_left() for p in inv.products]
        used      = [p.age_days   for p in inv.products]
        bar_cols  = [C["red"]   if r <= 1
                     else C["amber"] if r <= 3
                     else C["teal"]  for r in remaining]
        fig, ax = plt.subplots(figsize=(10,3.4))
        fig.patch.set_facecolor("white"); ax.set_facecolor("#f9fafb")
        ax.bar(names, remaining, color=bar_cols,
               edgecolor="white", label="Days remaining")
        ax.bar(names, used, bottom=remaining,
               color="#E0E8E2", edgecolor="white",
               alpha=0.5, label="Days already used")
        ax.set_ylabel("Days", fontsize=9); ax.legend(fontsize=9)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
        ax.set_title(
            "Green = Fresh   |   Amber = Expiring soon   |   Red = Expires today",
            fontsize=8, color=C["muted"])
        fig.tight_layout()
        FigureCanvasTkAgg(fig, cc).get_tk_widget().pack(
            fill="x", padx=8, pady=(0,8))
        plt.close(fig)

        sc = self._card(page); sc.pack(fill="x", padx=20, pady=(0,10))
        self._section(sc, "Expiry Status")
        self._table_hdr(sc,
            ["Product","Category","In Stock","Shelf Life","Age","Expires In","Status"],
            [14, 12, 10, 12, 10, 12, 16])
        for p in inv.products:
            dl = p.days_left()
            if   dl <= 1: st,sbg,sfg = "⚠ EXPIRING TODAY!", C["red_bg"], C["red"]
            elif dl <= 3: st,sbg,sfg = "⏰ Expiring soon",   C["amb_bg"], C["amber"]
            else:         st,sbg,sfg = "✅ Fresh",            C["grn_bg"], C["teal"]
            row = tk.Frame(sc, bg=sbg, highlightthickness=1,
                           highlightbackground=C["border"])
            row.pack(fill="x", padx=14, pady=1)
            for val, w, col in [
                (p.name,                  14, C["text"]),
                (p.category,              12, C["muted"]),
                (f"{p.current_stock:.0f} {p.unit}", 10, C["text"]),
                (f"{p.shelf_life}d",       12, C["muted"]),
                (f"{p.age_days}d",         10, C["muted"]),
                (f"{dl}d",                12, sfg),
                (st,                      16, sfg),
            ]:
                tk.Label(row, text=val, bg=sbg, fg=col,
                         font=("Segoe UI",9), width=w,
                         anchor="w").pack(side="left", padx=4, pady=6)

        bc = self._card(page); bc.pack(fill="x", padx=20, pady=(0,20))
        self._section(bc, "Simulate Time Passing")
        tk.Label(bc,
                 text="Click the button below to advance the clock by 1 day.\n"
                      "Stock will age by 1 day. Anything that expires will be removed and logged.",
                 bg=C["card"], fg=C["muted"],
                 font=("Segoe UI",9), justify="left").pack(
                     anchor="w", padx=14, pady=(0,6))

        def advance():
            expired = self.inv.advance_day()
            if expired:
                details = "\n".join(f"  • {n}: {q:.0f} {u}" for n,q,u in expired)
                messagebox.showwarning("Spoilage!", f"Expired items removed:\n\n{details}")
            else:
                messagebox.showinfo("✅ All Good",
                                    "Everything aged 1 day. Nothing expired.")
            self.show_spoilage()

        self._btn(bc, "⏭  Advance 1 Day  &  Check Spoilage",
                  C["red"], advance).pack(padx=14, pady=10, anchor="w")

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root); style.theme_use("clam")
    style.configure("TCombobox",
                    fieldbackground="white", background="white",
                    foreground=C["text"], selectbackground=C["green"],
                    selectforeground="white", arrowcolor=C["muted"])
    style.map("TCombobox", fieldbackground=[("readonly","white")])
    style.configure("TScrollbar", background=C["border"],
                    troughcolor=C["bg"], arrowcolor=C["muted"])
    InventoryGUI(root)
    root.mainloop()
