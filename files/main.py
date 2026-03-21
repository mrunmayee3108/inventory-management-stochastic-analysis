"""
AgriStock — Agricultural Inventory Management System
Full Tkinter UI  ·  MySQL Backend  ·  Stochastic Analysis

Requirements:
    pip install mysql-connector-python
    mysql -u root -p < schema.sql   (run once)
    Edit DB_CONFIG in db.py with your password

Run:
    python main.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
import math

# ── our modules ──
import db

# ─────────────────────────────────────────────
#  COLOUR SYSTEM
# ─────────────────────────────────────────────
C = {
    "bg":       "#F4F7F4",
    "sidebar":  "#1C3A2A",
    "side_sel": "#2A5240",
    "primary":  "#2D6A4F",
    "accent":   "#40916C",
    "card":     "#FFFFFF",
    "border":   "#DDE8DF",
    "text":     "#1A2E22",
    "muted":    "#6B8F71",
    "danger":   "#C0392B",
    "warning":  "#D4890A",
    "success":  "#27AE60",
    "info":     "#2471A3",
    "purple":   "#7D3C98",
    "teal":     "#148F77",
    "red_bg":   "#FDEDEC",
    "amb_bg":   "#FEF9E7",
    "grn_bg":   "#EAFAF1",
    "blu_bg":   "#EBF5FB",
    "pur_bg":   "#F5EEF8",
}

FONTS = {
    "h1":    ("Segoe UI", 20, "bold"),
    "h2":    ("Segoe UI", 13, "bold"),
    "h3":    ("Segoe UI", 10, "bold"),
    "body":  ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "kpi":   ("Segoe UI", 20, "bold"),
}

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def card(parent, **kw):
    return tk.Frame(parent, bg=C["card"],
                    highlightthickness=1,
                    highlightbackground=C["border"], **kw)

def sec(parent, text):
    tk.Label(parent, text=text.upper(), bg=parent["bg"],
             fg=C["muted"], font=("Segoe UI", 8, "bold"),
             anchor="w").pack(fill="x", padx=4, pady=(10, 2))

def scrolled(parent):
    """Returns (outer_frame, inner_frame) with vertical scroll."""
    outer = tk.Frame(parent, bg=C["bg"])
    outer.pack(fill="both", expand=True)
    vsb  = ttk.Scrollbar(outer, orient="vertical")
    vsb.pack(side="right", fill="y")
    cv   = tk.Canvas(outer, bg=C["bg"], highlightthickness=0,
                     yscrollcommand=vsb.set)
    cv.pack(side="left", fill="both", expand=True)
    vsb.config(command=cv.yview)
    inner = tk.Frame(cv, bg=C["bg"])
    wid   = cv.create_window((0, 0), window=inner, anchor="nw")
    cv.bind("<Configure>", lambda e: cv.itemconfig(wid, width=e.width))
    inner.bind("<Configure>",
               lambda e: cv.configure(scrollregion=cv.bbox("all")))
    cv.bind_all("<MouseWheel>",
                lambda e: cv.yview_scroll(-1*(e.delta//120), "units"))
    return outer, inner

def draw_freshness(canvas, age, shelf, w=130, h=14):
    canvas.delete("all")
    canvas.config(width=w, height=h)
    rem   = max(0, shelf - age)
    ratio = rem / shelf if shelf > 0 else 0
    col   = C["success"] if ratio > 0.5 else (C["warning"] if ratio > 0.2 else C["danger"])
    canvas.create_rectangle(0, 0, w, h, fill="#E8F0EA", outline="")
    fw = int(ratio * w)
    if fw > 0:
        canvas.create_rectangle(0, 0, fw, h, fill=col, outline="")
    canvas.create_text(w//2, h//2,
                       text=f"{rem}d left",
                       font=("Segoe UI", 7, "bold"),
                       fill="white" if fw > 55 else C["text"])

def draw_hist(canvas, data, color, title="", W=None, H=None):
    """Draw a simple histogram on a canvas."""
    canvas.delete("all")
    canvas.update_idletasks()
    W = W or canvas.winfo_width() or 300
    H = H or canvas.winfo_height() or 150
    BINS = 15
    L, R, T, B = 40, 8, 20, 22

    canvas.create_rectangle(0, 0, W, H, fill="white", outline="")
    if title:
        canvas.create_text(W//2, 11, text=title,
                           font=("Segoe UI", 8, "bold"), fill=C["text"])
    if not data: return

    lo, hi = min(data), max(data)
    if lo == hi: lo -= 1; hi += 1

    counts = [0] * BINS
    for v in data:
        i = int((v - lo) / (hi - lo) * BINS)
        counts[min(i, BINS - 1)] += 1
    mc = max(counts) or 1

    bx = lambda i: L + i * (W - L - R) / BINS
    by = lambda c: T + (1 - c / mc) * (H - T - B)

    for i, c in enumerate(counts):
        canvas.create_rectangle(bx(i)+1, by(c), bx(i+1)-1, H-B,
                                 fill=color, outline="white")

    mean_v = sum(data) / len(data)
    mx = L + (mean_v - lo) / (hi - lo) * (W - L - R)
    canvas.create_line(mx, T, mx, H-B, fill=C["warning"], dash=(4,2), width=2)
    canvas.create_text(mx+3, T+8, text=f"avg={mean_v:.1f}",
                       fill=C["warning"], font=("Segoe UI", 7), anchor="w")

    canvas.create_line(L, T, L, H-B, fill=C["border"])
    canvas.create_line(L, H-B, W-R, H-B, fill=C["border"])
    canvas.create_text(L+2,  H-10, text=f"{lo:.0f}", anchor="w",
                       font=("Segoe UI", 7), fill=C["muted"])
    canvas.create_text(W-R-2, H-10, text=f"{hi:.0f}", anchor="e",
                       font=("Segoe UI", 7), fill=C["muted"])

def draw_line_chart(canvas, series, colors, labels=None,
                    safety=None, title=""):
    canvas.delete("all")
    canvas.update_idletasks()
    W = canvas.winfo_width() or 400
    H = canvas.winfo_height() or 200
    L, R, T, B = 40, 12, 20, 28

    canvas.create_rectangle(0, 0, W, H, fill="white", outline="")
    if title:
        canvas.create_text(W//2, 11, text=title,
                           font=("Segoe UI", 8, "bold"), fill=C["text"])
    if not series or not series[0]: return

    all_vals = [v for s in series for v in s]
    lo = min(all_vals); hi = max(all_vals)
    if lo == hi: lo -= 1; hi += 1
    lo -= (hi - lo) * 0.1; hi += (hi - lo) * 0.1
    n = len(series[0])

    def px(i): return L + (i / max(n-1, 1)) * (W - L - R)
    def py(v): return T + (1 - (v-lo)/(hi-lo)) * (H - T - B)

    for k in range(5):
        gv = lo + k * (hi - lo) / 4
        gy = py(gv)
        canvas.create_line(L, gy, W-R, gy, fill="#E8F0EA", dash=(3,3))
        canvas.create_text(L-4, gy, text=f"{int(gv)}",
                           fill=C["muted"], font=("Segoe UI", 7), anchor="e")

    if safety and lo < safety < hi:
        sy = py(safety)
        canvas.create_line(L, sy, W-R, sy,
                           fill=C["warning"], dash=(5,3), width=2)
        canvas.create_text(W-R-2, sy-7, text=f"Safety={int(safety)}",
                           fill=C["warning"], font=("Segoe UI", 7), anchor="e")

    for s, col, dash in zip(series, colors,
                             [None, (5,3), (2,2)]):
        pts = []
        for i, v in enumerate(s): pts += [px(i), py(v)]
        if len(pts) >= 4:
            kw = dict(fill=col, width=2, smooth=True)
            if dash: kw["dash"] = dash
            canvas.create_line(pts, **kw)
        if pts:
            canvas.create_oval(pts[-2]-4, pts[-1]-4,
                               pts[-2]+4, pts[-1]+4,
                               fill=col, outline="white", width=1)

    canvas.create_line(L, T, L, H-B, fill=C["border"])
    canvas.create_line(L, H-B, W-R, H-B, fill=C["border"])

    for i in range(0, n, max(1, n//8)):
        canvas.create_text(px(i), H-B+10, text=str(i+1),
                           fill=C["muted"], font=("Segoe UI", 7))

    if labels:
        lx = L
        for lab, col in zip(labels, colors):
            canvas.create_line(lx, H-10, lx+16, H-10, fill=col, width=2)
            canvas.create_text(lx+20, H-10, text=lab,
                               anchor="w", fill=col,
                               font=("Segoe UI", 8))
            lx += 100

# ─────────────────────────────────────────────
#  DIALOGS
# ─────────────────────────────────────────────

class DeliveryDialog(tk.Toplevel):
    def __init__(self, master, products):
        super().__init__(master)
        self.title("Record Delivery")
        self.configure(bg=C["bg"])
        self.geometry("380x320")
        self.resizable(False, False)
        self.result = None

        tk.Label(self, text="Record Inbound Delivery",
                 bg=C["bg"], fg=C["text"],
                 font=FONTS["h2"]).pack(pady=(14,8))

        f = card(self); f.pack(fill="x", padx=20, pady=4)
        fields = {}
        rows_def = [
            ("Product",  "combo", [p["name"] for p in products]),
            ("Quantity", "entry", ""),
            ("Supplier", "entry", ""),
            ("Age (days already)","entry","0"),
        ]
        for lbl, wtype, val in rows_def:
            row = tk.Frame(f, bg=C["card"])
            row.pack(fill="x", padx=12, pady=4)
            tk.Label(row, text=lbl, bg=C["card"], fg=C["muted"],
                     font=FONTS["small"], width=20, anchor="w").pack(side="left")
            if wtype == "combo":
                v = tk.StringVar(value=val[0] if val else "")
                w = ttk.Combobox(row, textvariable=v, values=val,
                                 state="readonly", width=16)
            else:
                v = tk.StringVar(value=val)
                w = tk.Entry(row, textvariable=v, bg="white",
                             fg=C["text"], font=FONTS["body"],
                             relief="solid", bd=1, width=18)
            w.pack(side="right")
            fields[lbl] = v

        self.fields = fields
        self.products = products

        tk.Button(self, text="Save Delivery",
                  bg=C["primary"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=16, pady=7, cursor="hand2",
                  command=self._save).pack(pady=12)

    def _save(self):
        try:
            pname = self.fields["Product"].get()
            prod  = next(p for p in self.products if p["name"] == pname)
            qty   = float(self.fields["Quantity"].get())
            age   = int(self.fields["Age (days already)"].get())
            note  = self.fields["Supplier"].get()
            db.add_batch(prod["id"], qty, age, note)
            messagebox.showinfo("Saved",
                f"Delivery of {qty} {prod['unit']} of {pname} recorded!")
            self.result = True
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


class SaleDialog(tk.Toplevel):
    def __init__(self, master, products):
        super().__init__(master)
        self.title("Record Sale")
        self.configure(bg=C["bg"])
        self.geometry("380x300")
        self.resizable(False, False)
        self.result = None

        tk.Label(self, text="Record Sale",
                 bg=C["bg"], fg=C["text"],
                 font=FONTS["h2"]).pack(pady=(14,8))

        f = card(self); f.pack(fill="x", padx=20, pady=4)
        fields = {}
        rows_def = [
            ("Product",  "combo", [p["name"] for p in products]),
            ("Quantity", "entry", ""),
            ("Buyer",    "entry", ""),
        ]
        for lbl, wtype, val in rows_def:
            row = tk.Frame(f, bg=C["card"])
            row.pack(fill="x", padx=12, pady=4)
            tk.Label(row, text=lbl, bg=C["card"], fg=C["muted"],
                     font=FONTS["small"], width=20, anchor="w").pack(side="left")
            if wtype == "combo":
                v = tk.StringVar(value=val[0] if val else "")
                w = ttk.Combobox(row, textvariable=v, values=val,
                                 state="readonly", width=16)
            else:
                v = tk.StringVar()
                w = tk.Entry(row, textvariable=v, bg="white",
                             fg=C["text"], font=FONTS["body"],
                             relief="solid", bd=1, width=18)
            w.pack(side="right")
            fields[lbl] = v

        self.fields = fields
        self.products = products

        tk.Button(self, text="Record Sale",
                  bg=C["teal"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  padx=16, pady=7, cursor="hand2",
                  command=self._save).pack(pady=12)

    def _save(self):
        try:
            pname = self.fields["Product"].get()
            prod  = next(p for p in self.products if p["name"] == pname)
            qty   = float(self.fields["Quantity"].get())
            buyer = self.fields["Buyer"].get()
            sold, stockout = db.sell_stock(prod["id"], qty, buyer)
            if stockout > 0:
                messagebox.showwarning("Partial Sale",
                    f"Sold {sold} {prod['unit']}. "
                    f"Stockout: {stockout} {prod['unit']} not available!")
            else:
                messagebox.showinfo("Sale Recorded",
                    f"Sold {sold} {prod['unit']} of {pname} to {buyer}")
            self.result = True
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


class SimulationWindow(tk.Toplevel):
    """Full stochastic simulation window with live charts."""

    def __init__(self, master, products):
        super().__init__(master)
        self.title("Stochastic Analysis — AgriStock")
        self.configure(bg=C["bg"])
        self.geometry("1100x720")
        self.products = products

        self._running  = False
        self._drought  = False
        self._after_id = None
        self._stock    = 0
        self._age      = 0
        self._day      = 0
        self._P        = {}

        self._h_stock   = []
        self._h_harvest = []
        self._h_demand  = []
        self._h_profit  = []
        self._t_profit  = 0.0
        self._t_sold    = 0
        self._t_demand  = 0
        self._t_spoiled = 0
        self._t_recv    = 0

        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=C["sidebar"], height=46)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="Stochastic Inventory Analysis",
                 bg=C["sidebar"], fg="white",
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=14)
        self.weather_var = tk.StringVar(value="☀  Normal conditions")
        tk.Label(hdr, textvariable=self.weather_var,
                 bg=C["sidebar"], fg="#A8D8B0",
                 font=("Segoe UI", 10, "bold")).pack(side="right", padx=14)

        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)

        # ── SIDEBAR ──
        sb = tk.Frame(body, bg=C["sidebar"], width=220)
        sb.pack(side="left", fill="y"); sb.pack_propagate(False)

        tk.Label(sb, text="Product", bg=C["sidebar"], fg="#A8C9B0",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=12, pady=(12,2))
        self.prod_var = tk.StringVar()
        cb = ttk.Combobox(sb, textvariable=self.prod_var,
                          values=[p["name"] for p in self.products],
                          state="readonly", font=FONTS["small"], width=22)
        cb.pack(padx=10, pady=(0,8))
        if self.products:
            self.prod_var.set(self.products[0]["name"])

        tk.Label(sb, text="Simulation days", bg=C["sidebar"],
                 fg="#A8C9B0", font=("Segoe UI", 8, "bold")
                 ).pack(anchor="w", padx=12, pady=(6,2))
        self.days_var = tk.IntVar(value=60)
        tk.Spinbox(sb, textvariable=self.days_var, from_=10, to=365,
                   bg="white", fg=C["text"], font=FONTS["small"],
                   width=8, relief="solid", bd=1).pack(padx=10, anchor="w")

        tk.Label(sb, text="Speed (ms/day)", bg=C["sidebar"],
                 fg="#A8C9B0", font=("Segoe UI", 8, "bold")
                 ).pack(anchor="w", padx=12, pady=(6,2))
        self.speed_var = tk.IntVar(value=100)
        tk.Scale(sb, variable=self.speed_var, from_=20, to=600,
                 orient="horizontal", bg=C["sidebar"],
                 troughcolor="#2A5240", highlightthickness=0,
                 fg="white", length=190).pack(padx=10)

        tk.Frame(sb, bg="#2A5240", height=1).pack(fill="x", padx=10, pady=6)

        # KPI mini display
        self.kpi_vars = {}
        kpis = [("Day","—"),("Stock","—"),("Sold","—"),
                ("Spoiled","0"),("Stockout","0"),("Profit","—"),
                ("Total ₹","—"),("Service","—"),("Waste %","—"),("CR","—")]
        for lbl, val in kpis:
            row = tk.Frame(sb, bg=C["sidebar"])
            row.pack(fill="x", padx=12, pady=1)
            tk.Label(row, text=lbl, bg=C["sidebar"], fg="#6B9E75",
                     font=("Segoe UI", 8), width=9, anchor="w").pack(side="left")
            v = tk.StringVar(value=val)
            self.kpi_vars[lbl] = v
            tk.Label(row, textvariable=v, bg=C["sidebar"], fg="white",
                     font=("Segoe UI", 9, "bold")).pack(side="left")

        tk.Frame(sb, bg="#2A5240", height=1).pack(fill="x", padx=10, pady=6)

        # Buttons
        def sbtn(txt, bg, fg, cmd):
            tk.Button(sb, text=txt, bg=bg, fg=fg,
                      font=("Segoe UI", 9, "bold"), relief="flat",
                      pady=7, cursor="hand2",
                      command=cmd).pack(fill="x", padx=10, pady=2)

        sbtn("▶  Run simulation",  "#27AE60","white", self._do_run)
        sbtn("⏸  Pause",          "#D4890A","white", self._do_pause)
        sbtn("↺  Reset",          "#555555","white", self._do_reset)

        self.drought_btn = tk.Button(
            sb, text="🌵  Trigger Drought",
            bg=C["red_bg"], fg=C["danger"],
            font=("Segoe UI", 9, "bold"), relief="solid", bd=1,
            pady=7, cursor="hand2", command=self._toggle_drought)
        self.drought_btn.pack(fill="x", padx=10, pady=2)

        sbtn("🎲  Monte Carlo (300)", "#2471A3","white", self._do_monte_carlo)
        sbtn("🔬  What-If analysis", "#7D3C98","white", self._do_whatif)
        sbtn("🎯  Optimal safety stock","#148F77","white",self._do_optimal_ss)

        self.status_var = tk.StringVar(value="Select a product and press ▶ Run")
        tk.Label(sb, textvariable=self.status_var,
                 bg="#142B1E", fg="#A8C9B0",
                 font=("Segoe UI", 8), wraplength=200,
                 justify="left", padx=8, pady=6
                 ).pack(fill="x", side="bottom", padx=8, pady=8)

        # ── RIGHT: charts ──
        right = tk.Frame(body, bg=C["bg"])
        right.pack(fill="both", expand=True, padx=8, pady=8)
        right.rowconfigure(0, weight=3)
        right.rowconfigure(1, weight=2)
        right.columnconfigure(0, weight=1)

        def chart_card(parent, row, col=0, padx=0, pady=0, rs=1, cs=1):
            f = card(parent)
            f.grid(row=row, column=col, padx=padx, pady=pady,
                   rowspan=rs, columnspan=cs, sticky="nsew")
            f.rowconfigure(0, weight=1); f.columnconfigure(0, weight=1)
            cv = tk.Canvas(f, bg="white", highlightthickness=0)
            cv.grid(sticky="nsew", padx=4, pady=4)
            return cv

        self.c_stock   = chart_card(right, 0, pady=(0,4))
        bot = tk.Frame(right, bg=C["bg"])
        bot.grid(row=1, column=0, sticky="nsew")
        bot.columnconfigure(0, weight=1); bot.columnconfigure(1, weight=1)
        bot.rowconfigure(0, weight=1)
        self.c_harvest = chart_card(bot, 0, 0, padx=(0,4))
        self.c_profit  = chart_card(bot, 0, 1)

    # ── SIMULATION CONTROL ──

    def _get_product(self):
        name = self.prod_var.get()
        return next((p for p in self.products if p["name"] == name), None)

    def _do_run(self):
        if self._running: return
        P = self._get_product()
        if not P:
            messagebox.showwarning("No product", "Please select a product first.")
            return
        self._P = P
        if self._day == 0:
            self._stock = P["safety_stock"]
            self._age   = 0
            self._t_profit = self._t_sold = self._t_demand = 0
            self._t_spoiled = self._t_recv = 0
            self._h_stock = []; self._h_harvest = []
            self._h_demand = []; self._h_profit = []
            cr = db.critical_ratio(P)
            self.kpi_vars["CR"].set(f"{cr}")
        self._running = True
        self.status_var.set("Running…")
        self._tick()

    def _do_pause(self):
        self._running = False
        if self._after_id: self.after_cancel(self._after_id)
        self.status_var.set("Paused — press ▶ Run to continue")

    def _do_reset(self):
        self._do_pause()
        self._day = self._stock = self._age = 0
        self._t_profit = self._t_sold = self._t_demand = 0
        self._t_spoiled = self._t_recv = 0
        self._h_stock = self._h_harvest = self._h_demand = self._h_profit = []
        self._drought = False
        self.weather_var.set("☀  Normal conditions")
        self.drought_btn.config(text="🌵  Trigger Drought",
                                bg=C["red_bg"], fg=C["danger"])
        for k, v in self.kpi_vars.items(): v.set("—" if k != "Day" else "0")
        for cv in [self.c_stock, self.c_harvest, self.c_profit]:
            cv.delete("all")
            cv.create_text(cv.winfo_width()//2 or 200, 80,
                           text="Press ▶ Run to start",
                           fill=C["muted"], font=FONTS["body"])
        self.status_var.set("Reset. Press ▶ Run to start.")

    def _toggle_drought(self):
        if self._day == 0:
            self.status_var.set("Start simulation first!"); return
        self._drought = not self._drought
        if self._drought:
            self.drought_btn.config(text="✅  End Drought",
                                    bg=C["grn_bg"], fg=C["success"])
            self.weather_var.set("🌵  DROUGHT ACTIVE")
            pct = int(self._P.get("drought_factor", 0.3) * 100)
            self.status_var.set(f"Drought! Harvest = {pct}% of normal.\nSafety stock raised 80%.")
        else:
            self.drought_btn.config(text="🌵  Trigger Drought",
                                    bg=C["red_bg"], fg=C["danger"])
            self.weather_var.set("☀  Normal conditions")
            self.status_var.set("Drought ended. Normal supply resumed.")

    def _tick(self):
        if not self._running: return
        if self._day >= self.days_var.get():
            self._running = False
            svc = db.service_level(self._t_sold, self._t_demand)
            wst = db.waste_rate(self._t_spoiled, self._t_recv)
            self.status_var.set(
                f"Done! {self._day} days\n"
                f"Profit ₹{self._t_profit:,.0f}\n"
                f"Service {svc}%  Waste {wst}%")
            return

        self._day += 1
        self._stock, self._age, res = db.simulate_one_day(
            self._stock, self._age, self._day, self._P, self._drought)

        self._t_profit  += res["profit"]
        self._t_sold    += res["sold"]
        self._t_demand  += res["demand"]
        self._t_spoiled += res["spoiled"]
        self._t_recv    += res["harvest"]

        self._h_stock.append(res["stock"])
        self._h_harvest.append(res["harvest"])
        self._h_demand.append(res["demand"])
        self._h_profit.append(self._t_profit)

        svc  = db.service_level(self._t_sold, self._t_demand)
        wst  = db.waste_rate(self._t_spoiled, self._t_recv)
        sign = "+" if res["profit"] >= 0 else ""

        self.kpi_vars["Day"].set(str(self._day))
        self.kpi_vars["Stock"].set(str(res["stock"]))
        self.kpi_vars["Sold"].set(str(res["sold"]))
        self.kpi_vars["Spoiled"].set(str(res["spoiled"]))
        self.kpi_vars["Stockout"].set(str(res["stockout"]))
        self.kpi_vars["Profit"].set(f"{sign}₹{res['profit']:,.0f}")
        self.kpi_vars["Total ₹"].set(f"₹{self._t_profit:,.0f}")
        self.kpi_vars["Service"].set(f"{svc}%")
        self.kpi_vars["Waste %"].set(f"{wst}%")

        draw_line_chart(self.c_stock,
                        [self._h_stock],
                        [C["info"]],
                        safety=self._P.get("safety_stock"),
                        title="Stock level over time")
        draw_line_chart(self.c_harvest,
                        [self._h_harvest, self._h_demand],
                        [C["primary"], C["warning"]],
                        labels=["Harvest", "Demand"],
                        title="Harvest vs Demand")
        draw_line_chart(self.c_profit,
                        [self._h_profit],
                        [C["purple"]],
                        title="Cumulative Profit (₹)")

        self._after_id = self.after(self.speed_var.get(), self._tick)

    # ── MONTE CARLO ──

    def _do_monte_carlo(self):
        P = self._get_product()
        if not P:
            messagebox.showwarning("No product", "Select a product first.")
            return

        win = tk.Toplevel(self)
        win.title("Monte Carlo Results")
        win.configure(bg=C["bg"])
        win.geometry("760x540")

        prog_var = tk.DoubleVar(value=0)
        status_v = tk.StringVar(value="Running 300 simulations…")
        tk.Label(win, textvariable=status_v, bg=C["bg"],
                 fg=C["text"], font=FONTS["h2"]).pack(pady=(16,4))
        tk.Label(win, text=f"Product: {P['name']}  ·  "
                            f"Critical Ratio = {db.critical_ratio(P)}",
                 bg=C["bg"], fg=C["muted"],
                 font=FONTS["small"]).pack()
        pb = ttk.Progressbar(win, variable=prog_var,
                             maximum=100, length=400)
        pb.pack(pady=8)

        results_frame = tk.Frame(win, bg=C["bg"])
        results_frame.pack(fill="both", expand=True, padx=16, pady=4)

        def run_sim():
            res = db.run_monte_carlo(P, n_runs=300,
                                     days=self.days_var.get(),
                                     progress_cb=lambda p: prog_var.set(p))
            win.after(0, lambda: show_results(res))

        def show_results(res):
            status_v.set(f"Complete — avg profit ₹{res['p_avg']:,.0f}  |  "
                         f"service {res['svc_avg']}%  |  waste {res['wst_avg']}%")
            pb.pack_forget()

            # KPI grid
            kf = tk.Frame(results_frame, bg=C["bg"])
            kf.pack(fill="x", pady=(0,8))
            stats = [
                ("Avg profit",    f"₹{res['p_avg']:,.0f}",  C["info"]),
                ("Std deviation", f"₹{res['p_std']:,.0f}",  C["warning"]),
                ("Best run",      f"₹{res['p_best']:,.0f}", C["success"]),
                ("Worst run",     f"₹{res['p_worst']:,.0f}",C["danger"]),
                ("Avg service",   f"{res['svc_avg']}%",     C["teal"]),
                ("Avg waste",     f"{res['wst_avg']}%",     C["danger"]),
            ]
            for i, (lbl, val, col) in enumerate(stats):
                kf.columnconfigure(i, weight=1)
                c = card(kf)
                c.grid(row=0, column=i, padx=3, sticky="ew")
                tk.Label(c, text=lbl, bg=C["card"], fg=C["muted"],
                         font=FONTS["small"]).pack(anchor="w", padx=8, pady=(6,0))
                tk.Label(c, text=val, bg=C["card"], fg=col,
                         font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=8, pady=(0,6))

            # Histograms
            hf = tk.Frame(results_frame, bg=C["bg"])
            hf.pack(fill="both", expand=True)
            hf.columnconfigure(0, weight=2)
            hf.columnconfigure(1, weight=1)
            hf.columnconfigure(2, weight=1)
            hf.rowconfigure(0, weight=1)

            for col_idx, (data, color, title) in enumerate([
                (res["profits"],  C["info"],    "Profit distribution (₹)"),
                (res["services"], C["success"], "Service level (%)"),
                (res["wastes"],   C["danger"],  "Waste rate (%)"),
            ]):
                cf = card(hf)
                cf.grid(row=0, column=col_idx, sticky="nsew",
                        padx=(0,4) if col_idx<2 else 0)
                cf.rowconfigure(0, weight=1); cf.columnconfigure(0, weight=1)
                cv = tk.Canvas(cf, bg="white", highlightthickness=0)
                cv.grid(sticky="nsew", padx=4, pady=4)
                win.update_idletasks()
                draw_hist(cv, data, color, title)

        threading.Thread(target=run_sim, daemon=True).start()

    # ── WHAT-IF ──

    def _do_whatif(self):
        P = self._get_product()
        if not P:
            messagebox.showwarning("No product", "Select a product first.")
            return

        win = tk.Toplevel(self)
        win.title("What-If: Normal vs Drought")
        win.configure(bg=C["bg"])
        win.geometry("500x380")

        tk.Label(win, text="What-If Analysis",
                 bg=C["bg"], fg=C["text"],
                 font=FONTS["h2"]).pack(pady=(14,4))
        tk.Label(win, text=f"{P['name']}  ·  200 Monte Carlo runs each",
                 bg=C["bg"], fg=C["muted"],
                 font=FONTS["small"]).pack()

        status_v = tk.StringVar(value="Running simulations… please wait")
        tk.Label(win, textvariable=status_v, bg=C["bg"],
                 fg=C["muted"], font=FONTS["small"]).pack(pady=4)
        pb = ttk.Progressbar(win, mode="indeterminate", length=300)
        pb.pack(); pb.start()

        def run():
            wi = db.run_what_if(P, n_runs=200)
            win.after(0, lambda: show(wi))

        def show(wi):
            pb.stop(); pb.pack_forget()
            status_v.set("Complete")

            sf = tk.Frame(win, bg=C["bg"])
            sf.pack(fill="x", padx=20, pady=8)
            sf.columnconfigure(0,weight=1);sf.columnconfigure(1,weight=1);sf.columnconfigure(2,weight=1)

            for ci, (h, col) in enumerate([("Metric","#888"),
                                            ("☀  Normal", C["success"]),
                                            ("🌵  Drought",C["danger"])]):
                tk.Label(sf, text=h, bg=C["bg"], fg=col,
                         font=("Segoe UI", 10, "bold")
                         ).grid(row=0, column=ci, pady=(0,6))

            rows = [
                ("Avg total profit",
                 f"₹{wi['normal']['p_avg']:,.0f}",
                 f"₹{wi['drought']['p_avg']:,.0f}"),
                ("Service level",
                 f"{wi['normal']['svc_avg']}%",
                 f"{wi['drought']['svc_avg']}%"),
                ("Waste rate",
                 f"{wi['normal']['wst_avg']}%",
                 f"{wi['drought']['wst_avg']}%"),
            ]
            for ri, (lbl, nv, dv) in enumerate(rows, 1):
                tk.Label(sf, text=lbl, bg=C["bg"], fg=C["muted"],
                         font=FONTS["small"]).grid(row=ri, column=0,
                         sticky="w", pady=4)
                tk.Label(sf, text=nv, bg=C["bg"], fg=C["success"],
                         font=("Segoe UI",12,"bold")).grid(row=ri, column=1)
                tk.Label(sf, text=dv, bg=C["bg"], fg=C["danger"],
                         font=("Segoe UI",12,"bold")).grid(row=ri, column=2)

            impact = tk.Frame(win, bg=C["amb_bg"],
                              highlightthickness=1,
                              highlightbackground=C["warning"])
            impact.pack(fill="x", padx=20, pady=6)
            tk.Label(impact,
                     text=f"Drought costs ₹{wi['profit_loss']:,.0f} in profit\n"
                          f"Service level drops {wi['svc_drop']}%  |  "
                          f"Waste rises {wi['waste_rise']}%",
                     bg=C["amb_bg"], fg=C["warning"],
                     font=("Segoe UI", 10, "bold"),
                     justify="center").pack(pady=10)

            tk.Label(win,
                     text=f"Drought factor = {int(P['drought_factor']*100)}% of normal supply.\n"
                          f"Safety stock auto-rises 80% during drought.",
                     bg=C["bg"], fg=C["muted"],
                     font=FONTS["small"], justify="center").pack()

            tk.Button(win, text="Close", bg=C["primary"], fg="white",
                      font=("Segoe UI",9,"bold"), relief="flat",
                      padx=16, pady=6, command=win.destroy).pack(pady=10)

        threading.Thread(target=run, daemon=True).start()

    # ── OPTIMAL SAFETY STOCK ──

    def _do_optimal_ss(self):
        P = self._get_product()
        if not P:
            messagebox.showwarning("No product","Select a product first."); return

        target = simpledialog.askfloat(
            "Target Service Level",
            "Enter desired service level (e.g. 0.95 for 95%):",
            minvalue=0.5, maxvalue=1.0, initialvalue=0.95)
        if not target: return

        self.status_var.set("Calculating optimal safety stock…")
        self.update_idletasks()

        def calc():
            opt = db.optimal_safety_stock(P, target_service=target)
            self.after(0, lambda: messagebox.showinfo(
                "Optimal Safety Stock",
                f"Product: {P['name']}\n"
                f"Target service level: {target*100:.0f}%\n"
                f"Recommended safety stock: {opt} {P['unit']}\n"
                f"(Current safety stock: {P['safety_stock']} {P['unit']})"))
            self.status_var.set(f"Optimal SS = {opt} {P['unit']}")

        threading.Thread(target=calc, daemon=True).start()


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────

class AgriApp:

    def __init__(self, root):
        self.root = root
        self.root.title("AgriStock — Inventory Management")
        self.root.geometry("1280x800")
        self.root.configure(bg=C["bg"])
        self.root.minsize(1000, 650)

        self._products = []
        self._load_products()
        self._build()
        self._clock_tick()
        self._refresh_alerts()

    def _load_products(self):
        try:
            self._products = db.get_stock_summary()
        except Exception as e:
            messagebox.showerror("DB Error",
                f"Cannot load products from MySQL.\n\n{e}\n\n"
                "Check db.py DB_CONFIG and run schema.sql first.")
            self._products = []

    def _build(self):
        # Top bar
        topbar = tk.Frame(self.root, bg=C["sidebar"], height=52)
        topbar.pack(fill="x"); topbar.pack_propagate(False)

        tk.Label(topbar, text="🌿  AgriStock",
                 bg=C["sidebar"], fg="white",
                 font=("Segoe UI",15,"bold")).pack(side="left", padx=18)
        tk.Label(topbar, text="Agricultural Inventory Management",
                 bg=C["sidebar"], fg="#A8C9B0",
                 font=("Segoe UI",10)).pack(side="left")

        self.clock_var = tk.StringVar()
        tk.Label(topbar, textvariable=self.clock_var,
                 bg=C["sidebar"], fg="#A8C9B0",
                 font=("Segoe UI",10)).pack(side="right", padx=18)

        self.alert_badge_var = tk.StringVar(value="")
        self.alert_badge_lbl = tk.Label(topbar, textvariable=self.alert_badge_var,
                 bg=C["danger"], fg="white",
                 font=("Segoe UI",9,"bold"),
                 cursor="hand2")

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self.content = tk.Frame(body, bg=C["bg"])
        self.content.pack(side="left", fill="both", expand=True)

        self._show("Dashboard")

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=C["sidebar"], width=200)
        sb.pack(side="left", fill="y"); sb.pack_propagate(False)

        tk.Frame(sb, bg=C["sidebar"], height=10).pack()

        self._nav_btns = {}
        nav = [("Dashboard","📊"),("Stock Tracker","📦"),
               ("Orders","🚚"),("Alerts","🔔"),
               ("Analysis","📈"),("Stochastic","🎲"),
               ("Settings","⚙️")]
        for lbl, icon in nav:
            b = tk.Button(sb, text=f"  {icon}  {lbl}",
                          bg=C["sidebar"], fg="white",
                          font=("Segoe UI",10), relief="flat",
                          anchor="w", padx=14, pady=9,
                          cursor="hand2",
                          activebackground=C["side_sel"],
                          activeforeground="white",
                          command=lambda l=lbl: self._show(l))
            b.pack(fill="x")
            self._nav_btns[lbl] = b

        tk.Frame(sb, bg=C["sidebar"]).pack(fill="y", expand=True)

        # Refresh button
        tk.Button(sb, text="  ↺  Refresh data",
                  bg="#142B1E", fg="#A8C9B0",
                  font=("Segoe UI",9), relief="flat",
                  anchor="w", padx=14, pady=8,
                  cursor="hand2",
                  command=self._refresh).pack(fill="x")

        # Weather
        wf = tk.Frame(sb, bg="#142B1E", padx=10, pady=8)
        wf.pack(fill="x")
        tk.Label(wf, text="☀  Today's Weather",
                 bg="#142B1E", fg="#A8C9B0",
                 font=("Segoe UI",8,"bold")).pack(anchor="w")
        tk.Label(wf, text="34°C · Clear · Normal harvest expected",
                 bg="#142B1E", fg="#6B9E75",
                 font=("Segoe UI",8), wraplength=175,
                 justify="left").pack(anchor="w", pady=(2,0))

    def _show(self, name):
        for l, b in self._nav_btns.items():
            b.config(bg=C["side_sel"] if l == name else C["sidebar"])
        for w in self.content.winfo_children():
            w.destroy()
        {
            "Dashboard":    self._page_dashboard,
            "Stock Tracker":self._page_stock,
            "Orders":       self._page_orders,
            "Alerts":       self._page_alerts,
            "Analysis":     self._page_analysis,
            "Stochastic":   self._page_stochastic,
            "Settings":     self._page_settings,
        }.get(name, self._page_dashboard)()

    def _refresh(self):
        self._load_products()
        for w in self.content.winfo_children(): w.destroy()
        # re-render current page
        active = next((l for l, b in self._nav_btns.items()
                       if b["bg"] == C["side_sel"]), "Dashboard")
        self._show(active)

    # ══════════════════════════════════════════
    #  DASHBOARD
    # ══════════════════════════════════════════

    def _page_dashboard(self):
        _, inner = scrolled(self.content)

        title_row = tk.Frame(inner, bg=C["bg"])
        title_row.pack(fill="x", padx=20, pady=(16,4))
        tk.Label(title_row, text="Dashboard", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(side="left")
        tk.Label(title_row, text=time.strftime("Today, %d %b %Y"),
                 bg=C["bg"], fg=C["muted"],
                 font=FONTS["body"]).pack(side="right", pady=8)

        # KPI cards
        prods   = self._products
        total_q = sum(p["total_qty"] for p in prods)
        low     = sum(1 for p in prods if p["total_qty"] < p["safety_stock"])

        try:
            profit_data = db.get_profit_summary() or {}
        except:
            profit_data = {}

        kf = tk.Frame(inner, bg=C["bg"])
        kf.pack(fill="x", padx=20, pady=(4,8))
        kpis = [
            ("Total stock",       f"{total_q:.0f} units",   C["primary"],  "All products"),
            ("Low stock items",   str(low),                  C["danger"],   "Below safety level"),
            ("Today's revenue",  f"₹{profit_data.get('revenue',0):,.0f}",
                                                             C["success"],  "From sales today"),
            ("Today's waste cost",f"₹{profit_data.get('waste_cost',0):,.0f}",
                                                             C["warning"],  "Spoilage losses"),
            ("Sales today",       str(profit_data.get("sale_count",0)),
                                                             C["info"],     "Transactions"),
            ("Stockouts today",   str(int(profit_data.get("total_stockout",0))),
                                                             C["purple"],   "Units unmet"),
        ]
        for i, (lbl, val, col, sub) in enumerate(kpis):
            kf.columnconfigure(i, weight=1)
            c = card(kf)
            c.grid(row=0, column=i, padx=4, pady=2, sticky="ew")
            tk.Label(c, text=lbl, bg=C["card"], fg=C["muted"],
                     font=FONTS["small"]).pack(anchor="w", padx=10, pady=(8,0))
            tk.Label(c, text=val, bg=C["card"], fg=col,
                     font=FONTS["kpi"]).pack(anchor="w", padx=10)
            tk.Label(c, text=sub, bg=C["card"], fg=C["muted"],
                     font=FONTS["small"]).pack(anchor="w", padx=10, pady=(0,8))

        # Middle row
        mid = tk.Frame(inner, bg=C["bg"])
        mid.pack(fill="x", padx=20, pady=4)
        mid.columnconfigure(0, weight=3); mid.columnconfigure(1, weight=2)

        # Stock bar chart
        sc = card(mid)
        sc.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        tk.Label(sc, text="Stock levels by product",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        self._draw_stock_bars(sc)

        # Quick actions
        qa = card(mid)
        qa.grid(row=0, column=1, sticky="nsew")
        tk.Label(qa, text="Quick actions",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        self._draw_quick_actions(qa)

        # Alerts preview
        bot = card(inner)
        bot.pack(fill="x", padx=20, pady=(4,20))
        tk.Label(bot, text="Recent alerts",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        self._alerts_preview(bot)

    def _draw_stock_bars(self, parent):
        cv = tk.Canvas(parent, bg=C["card"], height=240,
                       highlightthickness=0)
        cv.pack(fill="x", padx=12, pady=(0,12))
        cv.update_idletasks()
        W = cv.winfo_width() or 400
        prods   = self._products
        if not prods: return
        max_qty = max(p["total_qty"] for p in prods) or 1
        bar_h, gap, label_w = 20, 8, 110

        for i, p in enumerate(prods):
            y = 10 + i * (bar_h + gap)
            cv.create_text(label_w-6, y+bar_h//2,
                           text=p["name"], anchor="e",
                           font=("Segoe UI",9), fill=C["text"])
            cv.create_rectangle(label_w, y, W-70, y+bar_h,
                                 fill="#EFF4F0", outline="")
            ratio = p["total_qty"] / max_qty
            bw    = int((W-70-label_w) * ratio)
            col   = C["danger"] if p["total_qty"] < p["safety_stock"] else C["primary"]
            if bw > 0:
                cv.create_rectangle(label_w, y, label_w+bw, y+bar_h,
                                     fill=col, outline="")
            sx = label_w + int((W-70-label_w) * p["safety_stock"] / max_qty)
            cv.create_line(sx, y-2, sx, y+bar_h+2,
                           fill=C["warning"], width=2, dash=(4,2))
            cv.create_text(W-68, y+bar_h//2,
                           text=f"{p['total_qty']:.0f} {p['unit']}",
                           anchor="w", font=("Segoe UI",8), fill=C["muted"])

    def _draw_quick_actions(self, parent):
        actions = [
            ("+ Record Delivery",  C["primary"], C["grn_bg"],
             lambda: self._open_delivery()),
            ("+ Record Sale",      C["teal"],    C["blu_bg"],
             lambda: self._open_sale()),
            ("⚠  Mark as Spoiled", C["danger"],  C["red_bg"],
             lambda: messagebox.showinfo("Waste","Open waste recording form")),
            ("🎲  Stochastic Analysis", C["purple"], C["pur_bg"],
             lambda: self._show("Stochastic")),
            ("🔔  View All Alerts", C["warning"], C["amb_bg"],
             lambda: self._show("Alerts")),
        ]
        for lbl, fg, bg, cmd in actions:
            tk.Button(parent, text=lbl, bg=bg, fg=fg,
                      font=("Segoe UI",10,"bold"), relief="flat",
                      anchor="w", padx=14, pady=8,
                      cursor="hand2", command=cmd
                      ).pack(fill="x", padx=12, pady=3)
        tk.Frame(parent, bg=C["card"], height=6).pack()

    def _alerts_preview(self, parent):
        try:
            alerts = db.get_alerts()[:6]
        except:
            alerts = []
        type_styles = {
            "critical": (C["danger"],  "●"),
            "warning":  (C["warning"], "▲"),
            "info":     (C["success"], "✓"),
            "suggest":  (C["purple"],  "◆"),
        }
        for a in alerts:
            col, icon = type_styles.get(a["alert_type"], (C["muted"], "•"))
            row = tk.Frame(parent, bg=C["card"])
            row.pack(fill="x", padx=12, pady=2)
            tk.Label(row, text=icon, fg=col, bg=C["card"],
                     font=("Segoe UI",10)).pack(side="left")
            tk.Label(row, text=a["message"], fg=C["text"], bg=C["card"],
                     font=FONTS["small"], anchor="w",
                     wraplength=500, justify="left").pack(side="left", padx=6)
        tk.Frame(parent, bg=C["card"], height=6).pack()

    def _open_delivery(self):
        try:
            prods = db.get_all_products()
        except:
            prods = []
        dlg = DeliveryDialog(self.root, prods)
        self.root.wait_window(dlg)
        if dlg.result:
            self._refresh()

    def _open_sale(self):
        try:
            prods = db.get_all_products()
        except:
            prods = []
        dlg = SaleDialog(self.root, prods)
        self.root.wait_window(dlg)
        if dlg.result:
            self._refresh()

    # ══════════════════════════════════════════
    #  STOCK TRACKER
    # ══════════════════════════════════════════

    def _page_stock(self):
        top = tk.Frame(self.content, bg=C["bg"])
        top.pack(fill="x", padx=20, pady=(16,8))
        tk.Label(top, text="Stock Tracker", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(side="left")
        tk.Button(top, text="+ Record Delivery",
                  bg=C["primary"], fg="white",
                  font=("Segoe UI",9,"bold"), relief="flat",
                  padx=10, pady=5, cursor="hand2",
                  command=self._open_delivery).pack(side="right")
        tk.Button(top, text="+ Record Sale",
                  bg=C["teal"], fg="white",
                  font=("Segoe UI",9,"bold"), relief="flat",
                  padx=10, pady=5, cursor="hand2",
                  command=self._open_sale).pack(side="right", padx=8)

        # Table
        tc = card(self.content)
        tc.pack(fill="both", expand=True, padx=20, pady=(0,20))

        cols = ["Product","Category","Qty","Freshness","Expiry","Location","Status","Action"]
        col_w= [14,      10,        8,    16,          10,      12,        9,       10]

        hrow = tk.Frame(tc, bg="#EFF4F0")
        hrow.pack(fill="x")
        for h, w in zip(cols, col_w):
            tk.Label(hrow, text=h, bg="#EFF4F0", fg=C["muted"],
                     font=("Segoe UI",8,"bold"),
                     width=w, anchor="w").pack(side="left", padx=4, pady=5)

        vsb = ttk.Scrollbar(tc, orient="vertical")
        vsb.pack(side="right", fill="y")
        cv  = tk.Canvas(tc, bg=C["card"], highlightthickness=0,
                        yscrollcommand=vsb.set)
        cv.pack(fill="both", expand=True)
        vsb.config(command=cv.yview)
        rf  = tk.Frame(cv, bg=C["card"])
        cv.create_window((0,0), window=rf, anchor="nw")
        rf.bind("<Configure>",
                lambda e: cv.configure(scrollregion=cv.bbox("all")))

        cat_colors = {
            "Vegetable":(C["grn_bg"],C["primary"]),
            "Fruit":    (C["blu_bg"],C["info"]),
            "Dairy":    (C["pur_bg"],C["purple"]),
            "Bakery":   (C["amb_bg"],C["warning"]),
            "Grain":    ("#F5F0E8","#7D6608"),
        }
        import datetime
        today = datetime.date.today()

        for p in self._products:
            days_left = (p["nearest_expiry"] - today).days if p["nearest_expiry"] else 999
            low       = p["total_qty"] < p["safety_stock"]
            row_bg    = C["red_bg"] if days_left <= 1 else C["card"]

            row = tk.Frame(rf, bg=row_bg,
                           highlightthickness=1,
                           highlightbackground=C["border"])
            row.pack(fill="x", pady=1)

            tk.Label(row, text=p["name"], bg=row_bg, fg=C["text"],
                     font=("Segoe UI",9,"bold"),
                     width=col_w[0], anchor="w").pack(side="left", padx=4, pady=7)

            cbg, cfg = cat_colors.get(p["category"],(C["card"],C["muted"]))
            tk.Label(row, text=p["category"], bg=cbg, fg=cfg,
                     font=("Segoe UI",8,"bold"),
                     padx=5, pady=1).pack(side="left", padx=4)

            qcol = C["danger"] if low else C["text"]
            tk.Label(row, text=f"{p['total_qty']:.0f} {p['unit']}",
                     bg=row_bg, fg=qcol,
                     font=("Segoe UI",9,"bold"),
                     width=col_w[2], anchor="w").pack(side="left", padx=4)

            fc = tk.Canvas(row, bg=row_bg, highlightthickness=0,
                           width=130, height=14)
            fc.pack(side="left", padx=4, pady=6)
            draw_freshness(fc, p["max_age"], p["shelf_life"], 130, 14)

            exp_str = (str(p["nearest_expiry"]) if p["nearest_expiry"] else "—")
            tk.Label(row, text=exp_str, bg=row_bg, fg=C["muted"],
                     font=FONTS["small"],
                     width=col_w[4], anchor="w").pack(side="left", padx=4)

            tk.Label(row, text=p["location"], bg=row_bg, fg=C["muted"],
                     font=FONTS["small"],
                     width=col_w[5], anchor="w").pack(side="left", padx=4)

            if days_left <= 1:
                st, sbg, sfg = "Expiring!", C["red_bg"], C["danger"]
            elif low:
                st, sbg, sfg = "Low stock", C["amb_bg"], C["warning"]
            else:
                st, sbg, sfg = "Good", C["grn_bg"], C["success"]
            tk.Label(row, text=st, bg=sbg, fg=sfg,
                     font=("Segoe UI",8,"bold"), padx=6, pady=2
                     ).pack(side="left", padx=4)

            tk.Button(row, text="Order", bg=C["blu_bg"], fg=C["info"],
                      font=("Segoe UI",8,"bold"), relief="flat",
                      padx=6, pady=2, cursor="hand2",
                      command=lambda pid=p["id"]: (
                          db.check_reorder(pid),
                          messagebox.showinfo("Reorder", "Reorder checked and logged!")
                      )).pack(side="left", padx=4)

    # ══════════════════════════════════════════
    #  ORDERS
    # ══════════════════════════════════════════

    def _page_orders(self):
        tk.Label(self.content, text="Orders & Supply", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(anchor="w", padx=20, pady=(16,8))

        try:
            txns = db.get_recent_transactions(60)
        except:
            txns = []

        tc = card(self.content)
        tc.pack(fill="both", expand=True, padx=20, pady=(0,20))
        tk.Label(tc, text="Recent transactions",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))

        hdrs = ["Date","Product","Type","Qty","Value","Party","Notes"]
        hrow = tk.Frame(tc, bg="#EFF4F0")
        hrow.pack(fill="x", padx=12)
        for h in hdrs:
            tk.Label(hrow, text=h, bg="#EFF4F0", fg=C["muted"],
                     font=("Segoe UI",8,"bold"),
                     width=11, anchor="w").pack(side="left", padx=4, pady=5)

        type_colors = {
            "sale":     C["success"],
            "waste":    C["danger"],
            "delivery": C["info"],
            "stockout": C["warning"],
            "reorder":  C["purple"],
        }

        vsb = ttk.Scrollbar(tc, orient="vertical")
        vsb.pack(side="right", fill="y")
        cv  = tk.Canvas(tc, bg=C["card"], highlightthickness=0,
                        yscrollcommand=vsb.set)
        cv.pack(fill="both", expand=True)
        vsb.config(command=cv.yview)
        rf  = tk.Frame(cv, bg=C["card"])
        cv.create_window((0,0), window=rf, anchor="nw")
        rf.bind("<Configure>",
                lambda e: cv.configure(scrollregion=cv.bbox("all")))

        for t in txns:
            row = tk.Frame(rf, bg=C["card"],
                           highlightthickness=1,
                           highlightbackground=C["border"])
            row.pack(fill="x", pady=1)
            col = type_colors.get(t["txn_type"], C["muted"])
            vals = [
                str(t["txn_date"]),
                t["product_name"],
                t["txn_type"].upper(),
                f"{t['quantity']:.1f} {t['unit']}",
                f"₹{abs(t['total_value']):.0f}",
                t["party_name"] or "—",
                (t["notes"] or "")[:30],
            ]
            for i, v in enumerate(vals):
                fc = col if i == 2 else C["text"]
                tk.Label(row, text=v, bg=C["card"], fg=fc,
                         font=FONTS["small"] if i != 2 else ("Segoe UI",8,"bold"),
                         width=11, anchor="w").pack(side="left", padx=4, pady=5)

    # ══════════════════════════════════════════
    #  ALERTS
    # ══════════════════════════════════════════

    def _page_alerts(self):
        top = tk.Frame(self.content, bg=C["bg"])
        top.pack(fill="x", padx=20, pady=(16,8))
        tk.Label(top, text="Alerts", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(side="left")
        tk.Button(top, text="Check expiry now",
                  bg=C["warning"], fg="white",
                  font=("Segoe UI",9,"bold"), relief="flat",
                  padx=10, pady=5, cursor="hand2",
                  command=lambda: (db.generate_expiry_alerts(),
                                   self._refresh())).pack(side="right")

        _, inner = scrolled(self.content)

        try:
            alerts = db.get_alerts()
        except:
            alerts = []

        type_styles = {
            "critical": (C["red_bg"], C["danger"],  "CRITICAL","●"),
            "warning":  (C["amb_bg"], C["warning"], "WARNING", "▲"),
            "info":     (C["grn_bg"], C["success"], "INFO",    "✓"),
            "suggest":  (C["pur_bg"], C["purple"],  "TIP",     "◆"),
        }

        for a in alerts:
            bg, fg, tag, icon = type_styles.get(
                a["alert_type"], (C["card"], C["muted"], "NOTE", "•"))
            row = tk.Frame(inner, bg=bg,
                           highlightthickness=1,
                           highlightbackground=C["border"])
            row.pack(fill="x", padx=20, pady=3)

            left = tk.Frame(row, bg=bg, width=70)
            left.pack(side="left", fill="y", padx=8, pady=8)
            left.pack_propagate(False)
            tk.Label(left, text=icon, bg=bg, fg=fg,
                     font=("Segoe UI",14)).pack()
            tk.Label(left, text=tag, bg=bg, fg=fg,
                     font=("Segoe UI",7,"bold")).pack()

            mid = tk.Frame(row, bg=bg)
            mid.pack(side="left", fill="x", expand=True, pady=8)
            tk.Label(mid, text=a["message"], bg=bg, fg=C["text"],
                     font=("Segoe UI",10), wraplength=700,
                     justify="left", anchor="w").pack(anchor="w")
            ts = str(a["created_at"])[:16]
            tk.Label(mid, text=f"{a['product_name'] or 'System'}  ·  {ts}",
                     bg=bg, fg=fg, font=FONTS["small"]).pack(anchor="w")

            tk.Button(row, text="Mark read", bg=bg, fg=C["muted"],
                      font=("Segoe UI",8), relief="flat",
                      padx=8, pady=4, cursor="hand2",
                      command=lambda aid=a["id"], r=row: (
                          db.mark_alert_read(aid), r.destroy())
                      ).pack(side="right", padx=8)

    def _refresh_alerts(self):
        try:
            count = len([a for a in db.get_alerts()
                         if a["alert_type"]=="critical" and not a["is_read"]])
            if count:
                self.alert_badge_var.set(f"  {count} critical  ")
                self.alert_badge_lbl.pack(side="right", padx=6, pady=12)
            else:
                self.alert_badge_lbl.pack_forget()
        except:
            pass
        self.root.after(30000, self._refresh_alerts)

    # ══════════════════════════════════════════
    #  ANALYSIS
    # ══════════════════════════════════════════

    def _page_analysis(self):
        tk.Label(self.content, text="Analysis", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(anchor="w", padx=20, pady=(16,8))

        two = tk.Frame(self.content, bg=C["bg"])
        two.pack(fill="both", expand=True, padx=20, pady=(0,20))
        two.columnconfigure(0,weight=1); two.columnconfigure(1,weight=1)
        two.rowconfigure(0,weight=1);   two.rowconfigure(1,weight=1)

        def chart_card(row, col, padx=0, pady=0):
            f = card(two)
            f.grid(row=row, column=col, padx=padx, pady=pady, sticky="nsew")
            f.rowconfigure(1,weight=1); f.columnconfigure(0,weight=1)
            return f

        # Waste by product
        c1 = chart_card(0, 0, padx=(0,6), pady=(0,6))
        tk.Label(c1, text="Waste by product — last 30 days",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        cv1 = tk.Canvas(c1, bg="white", highlightthickness=0, height=180)
        cv1.pack(fill="x", padx=12, pady=(0,12))

        # Service level trend
        c2 = chart_card(0, 1, pady=(0,6))
        tk.Label(c2, text="Weekly service level %",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        cv2 = tk.Canvas(c2, bg="white", highlightthickness=0, height=180)
        cv2.pack(fill="x", padx=12, pady=(0,12))

        # Performance table
        c3 = chart_card(1, 0, padx=(0,6))
        tk.Label(c3, text="Product performance summary",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        self._perf_table(c3)

        # Profit breakdown
        c4 = chart_card(1, 1)
        tk.Label(c4, text="Today's profit breakdown",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        self._profit_breakdown(c4)

        # Draw charts after layout
        self.content.after(100, lambda: self._draw_analysis_charts(cv1, cv2))

    def _draw_analysis_charts(self, cv1, cv2):
        # Waste bar chart
        try:
            waste_data = db.get_waste_by_product()
        except:
            waste_data = []
        cv1.update_idletasks()
        W = cv1.winfo_width() or 350; H = 180
        L, B = 90, 28
        if waste_data:
            max_w = max(r["total_waste"] for r in waste_data) or 1
            bar_h, gap = 20, 8
            for i, r in enumerate(waste_data[:8]):
                y  = 10 + i * (bar_h + gap)
                bw = int(r["total_waste"] / max_w * (W - L - 10))
                cv1.create_text(L-6, y+bar_h//2,
                                text=r["name"][:12], anchor="e",
                                font=("Segoe UI",8), fill=C["text"])
                cv1.create_rectangle(L, y, W-10, y+bar_h,
                                     fill="#EFF4F0", outline="")
                if bw > 0:
                    cv1.create_rectangle(L, y, L+bw, y+bar_h,
                                         fill=C["danger"], outline="")
                cv1.create_text(L+bw+4, y+bar_h//2,
                                text=f"{r['total_waste']:.1f}",
                                anchor="w", font=("Segoe UI",7), fill=C["muted"])
        else:
            cv1.create_text(W//2, H//2, text="No waste data yet",
                            fill=C["muted"], font=FONTS["body"])

        # Service level line chart
        try:
            svc_data = db.get_weekly_service_level()
        except:
            svc_data = []
        cv2.update_idletasks()
        W2 = cv2.winfo_width() or 350; H2 = 180
        if svc_data:
            services = []
            for r in svc_data:
                total = r["sold"] + r["short"]
                svc   = round(r["sold"] / total * 100, 1) if total > 0 else 100
                services.append(svc)
            draw_line_chart(cv2, [services], [C["success"]],
                            title="Service level %")
        else:
            # Simulated fallback
            import random
            svcs = [round(85 + i + (hash(str(i))%10), 1) for i in range(8)]
            draw_line_chart(cv2, [svcs], [C["success"]],
                            title="Service level % (simulated)")

    def _perf_table(self, parent):
        hdrs = ["Product","Qty","Safety","Status"]
        hrow = tk.Frame(parent, bg="#EFF4F0")
        hrow.pack(fill="x", padx=12)
        for h in hdrs:
            tk.Label(hrow, text=h, bg="#EFF4F0", fg=C["muted"],
                     font=("Segoe UI",8,"bold"),
                     width=12, anchor="w").pack(side="left", padx=4, pady=4)
        for p in self._products:
            row = tk.Frame(parent, bg=C["card"],
                           highlightthickness=1,
                           highlightbackground=C["border"])
            row.pack(fill="x", padx=12, pady=1)
            low = p["total_qty"] < p["safety_stock"]
            vals = [p["name"],
                    f"{p['total_qty']:.0f} {p['unit']}",
                    f"{p['safety_stock']:.0f}",
                    "Low ⚠" if low else "Good ✓"]
            cols = [C["text"], C["text"], C["muted"],
                    C["danger"] if low else C["success"]]
            for v, c in zip(vals, cols):
                tk.Label(row, text=v, bg=C["card"], fg=c,
                         font=FONTS["small"], width=12,
                         anchor="w").pack(side="left", padx=4, pady=5)

    def _profit_breakdown(self, parent):
        try:
            d = db.get_profit_summary() or {}
        except:
            d = {}
        rev   = d.get("revenue", 0) or 0
        waste = d.get("waste_cost", 0) or 0
        so    = d.get("total_stockout", 0) or 0
        net   = rev - waste

        metrics = [
            ("Revenue",       f"₹{rev:,.0f}",   C["success"]),
            ("Waste losses",  f"₹{waste:,.0f}",  C["danger"]),
            ("Stockout units",f"{so:.0f} units", C["warning"]),
            ("Net profit",    f"₹{net:,.0f}",    C["primary"] if net>=0 else C["danger"]),
        ]
        for lbl, val, col in metrics:
            row = tk.Frame(parent, bg=C["card"])
            row.pack(fill="x", padx=12, pady=5)
            tk.Label(row, text=lbl, bg=C["card"], fg=C["muted"],
                     font=FONTS["small"], width=16, anchor="w").pack(side="left")
            tk.Label(row, text=val, bg=C["card"], fg=col,
                     font=("Segoe UI",12,"bold")).pack(side="right")
        tk.Frame(parent, bg=C["card"], height=6).pack()

    # ══════════════════════════════════════════
    #  STOCHASTIC PAGE
    # ══════════════════════════════════════════

    def _page_stochastic(self):
        tk.Label(self.content, text="Stochastic Analysis", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(anchor="w", padx=20, pady=(16,4))
        tk.Label(self.content,
                 text="Simulate inventory behaviour under uncertainty — "
                      "random supply, random demand, drought scenarios.",
                 bg=C["bg"], fg=C["muted"],
                 font=FONTS["body"]).pack(anchor="w", padx=20, pady=(0,16))

        try:
            prods = db.get_all_products()
        except:
            prods = []

        # Product cards
        grid = tk.Frame(self.content, bg=C["bg"])
        grid.pack(fill="x", padx=20)
        for i, p in enumerate(prods):
            grid.columnconfigure(i % 4, weight=1)
            c = card(grid)
            c.grid(row=i//4, column=i%4, padx=4, pady=4, sticky="ew")
            tk.Label(c, text=p["name"], bg=C["card"], fg=C["text"],
                     font=("Segoe UI",10,"bold")).pack(anchor="w", padx=10, pady=(8,2))
            cr = db.critical_ratio(p)
            cr_col = C["success"] if cr >= 0.5 else C["warning"]
            tk.Label(c, text=f"CR = {cr}  ·  Shelf {p['shelf_life']}d",
                     bg=C["card"], fg=cr_col,
                     font=FONTS["small"]).pack(anchor="w", padx=10)
            tk.Label(c, text=f"Safety stock: {p['safety_stock']} {p['unit']}",
                     bg=C["card"], fg=C["muted"],
                     font=FONTS["small"]).pack(anchor="w", padx=10, pady=(0,8))

        tk.Button(self.content,
                  text="🎲  Open Full Simulation Window",
                  bg=C["primary"], fg="white",
                  font=("Segoe UI",12,"bold"), relief="flat",
                  padx=20, pady=12, cursor="hand2",
                  command=lambda: SimulationWindow(self.root, prods)
                  ).pack(pady=20)

        # Explain CR
        info = card(self.content)
        info.pack(fill="x", padx=20, pady=(0,20))
        tk.Label(info, text="Understanding the Critical Ratio",
                 bg=C["card"], fg=C["text"],
                 font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        tk.Label(info,
                 text="CR = Stockout cost  ÷  (Stockout cost + Waste cost)\n\n"
                      "CR > 0.5 → Running out of stock hurts more than wasting — keep more stock.\n"
                      "CR < 0.5 → Waste is more costly — keep less stock.\n"
                      "CR = 0.5 → Both risks are equal — balance is optimal.",
                 bg=C["card"], fg=C["muted"],
                 font=FONTS["body"], justify="left"
                 ).pack(anchor="w", padx=12, pady=(0,12))

    # ══════════════════════════════════════════
    #  SETTINGS
    # ══════════════════════════════════════════

    def _page_settings(self):
        tk.Label(self.content, text="Settings", bg=C["bg"],
                 fg=C["text"], font=FONTS["h1"]).pack(anchor="w", padx=20, pady=(16,8))

        _, inner = scrolled(self.content)

        try:
            prods = db.get_all_products()
        except:
            prods = []

        self._setting_entries = {}

        for p in prods:
            pc = card(inner)
            pc.pack(fill="x", padx=20, pady=4)

            hdr = tk.Frame(pc, bg=C["card"])
            hdr.pack(fill="x", padx=12, pady=(8,4))
            tk.Label(hdr, text=p["name"], bg=C["card"], fg=C["text"],
                     font=("Segoe UI",11,"bold")).pack(side="left")
            tk.Label(hdr, text=f"{p['category']}  ·  {p['supplier']}",
                     bg=C["card"], fg=C["muted"],
                     font=FONTS["small"]).pack(side="left", padx=8)

            row_frame = tk.Frame(pc, bg=C["card"])
            row_frame.pack(fill="x", padx=12, pady=(0,8))

            fields = [
                ("Safety stock",       "safety_stock",  p["safety_stock"]),
                ("Reorder qty",        "reorder_qty",   p["reorder_qty"]),
                ("Shelf life (days)",  "shelf_life",    p["shelf_life"]),
                ("Sale price (₹)",     "sale_price",    p["sale_price"]),
                ("Waste cost (₹)",     "waste_cost",    p["waste_cost"]),
                ("Stockout cost (₹)",  "stockout_cost", p["stockout_cost"]),
                ("Avg supply/day",     "avg_supply",    p["avg_supply"]),
                ("Drought factor",     "drought_factor",p["drought_factor"]),
            ]
            entries = {}
            for col_idx, (lbl, key, val) in enumerate(fields):
                cf = tk.Frame(row_frame, bg=C["card"])
                cf.grid(row=0, column=col_idx, padx=8, sticky="w")
                row_frame.columnconfigure(col_idx, weight=1)
                tk.Label(cf, text=lbl, bg=C["card"], fg=C["muted"],
                         font=("Segoe UI",7,"bold")).pack(anchor="w")
                v = tk.StringVar(value=str(val))
                e = tk.Entry(cf, textvariable=v, bg="white",
                             fg=C["text"], font=FONTS["body"],
                             width=9, relief="solid", bd=1)
                e.pack()
                entries[key] = v

            self._setting_entries[p["id"]] = entries

            def save(pid=p["id"], ents=entries):
                try:
                    db.update_product_thresholds(
                        pid,
                        float(ents["safety_stock"].get()),
                        float(ents["reorder_qty"].get()),
                        int(ents["shelf_life"].get()))
                    db.update_product_costs(
                        pid,
                        float(ents["sale_price"].get()),
                        float(ents["waste_cost"].get()),
                        float(ents["stockout_cost"].get()),
                        0.05)
                    db.update_product_supply(
                        pid,
                        float(ents["avg_supply"].get()),
                        15, 60, 120,
                        float(ents["drought_factor"].get()))
                    messagebox.showinfo("Saved", "Settings saved to database!")
                    self._refresh()
                except Exception as ex:
                    messagebox.showerror("Error", str(ex))

            tk.Button(pc, text="Save", bg=C["primary"], fg="white",
                      font=("Segoe UI",9,"bold"), relief="flat",
                      padx=12, pady=4, cursor="hand2",
                      command=save).pack(anchor="e", padx=12, pady=(0,8))

    # ── CLOCK ──

    def _clock_tick(self):
        now = time.strftime("  %a %d %b %Y   %I:%M:%S %p  ")
        self.clock_var.set(now)
        self.root.after(1000, self._clock_tick)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TCombobox",
                    fieldbackground="white", background="white",
                    foreground=C["text"],
                    selectbackground=C["primary"],
                    selectforeground="white",
                    arrowcolor=C["muted"])
    style.map("TCombobox", fieldbackground=[("readonly","white")])
    style.configure("TScrollbar",
                    background=C["border"],
                    troughcolor=C["bg"],
                    arrowcolor=C["muted"])
    style.configure("TProgressbar",
                    troughcolor=C["border"],
                    background=C["primary"])

    app = AgriApp(root)
    root.mainloop()
