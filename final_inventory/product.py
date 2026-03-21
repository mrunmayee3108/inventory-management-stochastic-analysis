# ================================================================
# product.py  —  Product Classes
# ================================================================
# OOP Concepts:
#   Encapsulation : data + methods bundled inside the class
#   Inheritance   : PerishableProduct extends Product
#   Polymorphism  : is_expired() behaves differently in each class
# ================================================================


class Product:
    """Base class. Any item stored in a warehouse."""

    def __init__(self, name, category, unit, stock, reorder_point):
        self.name          = name
        self.category      = category
        self.unit          = unit
        self.current_stock = stock
        self.reorder_point = reorder_point

    def needs_reorder(self):
        return self.current_stock < self.reorder_point

    def add_stock(self, qty):
        self.current_stock += qty

    def remove_stock(self, qty):
        """Sell stock. Returns units actually sold."""
        sold = min(self.current_stock, qty)
        self.current_stock -= sold
        return sold

    def is_expired(self):
        """Base products never expire."""
        return False

    def __str__(self):
        return f"{self.name} — {self.current_stock} {self.unit}"


# ────────────────────────────────────────────────────────────────

class PerishableProduct(Product):
    """
    A product with a shelf life.

    INHERITANCE  : gets add_stock, remove_stock, needs_reorder for free.
    POLYMORPHISM : is_expired() overridden with real logic.

    The user only provides simple, real-world fields:
        name, category, unit, stock, reorder point, reorder qty,
        shelf life, sale price, average daily demand.

    Everything else (waste cost, stockout cost, demand variation,
    drought factor) is AUTO-CALCULATED internally.
    The user never needs to know about these.
    """

    def __init__(self, name, category, unit,
                 stock, reorder_point, reorder_qty,
                 shelf_life, sale_price, avg_demand):

        super().__init__(name, category, unit, stock, reorder_point)

        self.reorder_qty  = reorder_qty
        self.shelf_life   = shelf_life      # days before expiry
        self.sale_price   = sale_price
        self.avg_demand   = avg_demand
        self.age_days     = 0               # days the stock has been sitting

        # ── Auto-calculated (hidden from user) ────────────────────
        # Demand variation = 20% of average demand (industry standard assumption)
        self.demand_std = avg_demand * 0.20

        # Waste cost = 30% of sale price  (cost of 1 expired unit)
        self.waste_cost = round(sale_price * 0.30, 2)

        # Stockout cost = 60% of sale price  (lost revenue + goodwill)
        self.stockout_cost = round(sale_price * 0.60, 2)

        # During drought, farm produces only 30% of normal supply
        self.drought_factor = 0.30

    def is_expired(self):
        """Returns True when stock age reaches shelf life."""
        return self.age_days >= self.shelf_life

    def days_left(self):
        """Days remaining before this batch expires."""
        return max(0, self.shelf_life - self.age_days)

    def critical_ratio(self):
        """
        CR = Cu / (Cu + Co)
        Cu = stockout cost  (cost of running OUT)
        Co = waste cost     (cost of over-ordering)

        CR > 0.5  →  keep MORE stock  (running out is worse)
        CR < 0.5  →  keep LESS stock  (wasting is worse)
        """
        return round(self.stockout_cost / (self.stockout_cost + self.waste_cost), 3)


# ────────────────────────────────────────────────────────────────

def default_products():
    """Sample products loaded when the app starts."""
    #                   name            cat         unit   stk  rp   rq  shelf price demand
    return [
        PerishableProduct("Milk",         "Dairy",    "L",  140, 50, 100,  7,  35,  120),
        PerishableProduct("Strawberries", "Fruit",    "kg",  22, 15,  40,  3,  80,   60),
        PerishableProduct("Leafy Greens", "Vegetable","kg",  60, 30,  60,  4,  45,   80),
        PerishableProduct("Bread",        "Bakery",   "pcs", 38, 20,  50,  2,  25,   50),
        PerishableProduct("Tomatoes",     "Vegetable","kg",  85, 30,  60,  5,  35,   90),
        PerishableProduct("Mangoes",      "Fruit",    "kg",  55, 20,  50,  6,  70,   60),
    ]
