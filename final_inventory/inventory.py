# ================================================================
# inventory.py  —  Inventory Class
# ================================================================
# Manages all products and transaction history.
# Pure Python — no database, no libraries.
#
# OOP: Encapsulation — all warehouse operations are here.
# ================================================================

from datetime import datetime
from product import default_products, PerishableProduct


class Inventory:
    """
    The warehouse manager.

    self.products     — list of PerishableProduct objects
    self.transactions — list of dicts (activity log)
    """

    def __init__(self):
        self.products     = default_products()
        self.transactions = []

    # ── Find ──────────────────────────────────────────────────

    def get(self, name):
        """Find product by name. Returns None if not found."""
        for p in self.products:
            if p.name == name:
                return p
        return None

    # ── Stock changes ─────────────────────────────────────────

    def add_stock(self, name, qty):
        """Delivery received — add stock and reset age."""
        p = self.get(name)
        if p:
            p.add_stock(qty)
            p.age_days = 0
            self._log(name, "DELIVERY", qty, "Stock received")

    def sell_stock(self, name, qty):
        """Record a sale. Returns units actually sold."""
        p = self.get(name)
        if p:
            sold = p.remove_stock(qty)
            self._log(name, "SALE", sold, "Sold to customer")
            return sold
        return 0

    def add_product(self, product):
        """Add a new product to the warehouse."""
        self.products.append(product)
        self._log(product.name, "ADDED", product.current_stock, "New product added")

    def delete_product(self, name):
        """Remove a product completely. Returns True if found."""
        p = self.get(name)
        if p:
            self.products.remove(p)
            self._log(name, "DELETED", 0, "Product removed")
            return True
        return False

    # ── Spoilage ──────────────────────────────────────────────

    def advance_day(self):
        """
        Age all products by 1 day.
        Returns list of (name, qty, unit) for anything that expired.
        """
        expired = []
        for p in self.products:
            p.age_days += 1
            if p.is_expired() and p.current_stock > 0:
                expired.append((p.name, p.current_stock, p.unit))
                self._log(p.name, "SPOILED", p.current_stock, "Expired and removed")
                p.current_stock = 0
                p.age_days      = 0
        return expired

    # ── Alerts ────────────────────────────────────────────────

    def low_stock(self):
        """Products below their reorder point."""
        return [p for p in self.products if p.needs_reorder()]

    def expiring_soon(self):
        """Products expiring within 3 days."""
        return [p for p in self.products if 0 < p.days_left() <= 3]

    # ── Log ───────────────────────────────────────────────────

    def _log(self, name, action, qty, note):
        self.transactions.append({
            "time":    datetime.now().strftime("%d %b  %H:%M"),
            "product": name,
            "action":  action,
            "qty":     qty,
            "note":    note,
        })

    def recent_log(self, n=15):
        """Last n transactions, newest first."""
        return list(reversed(self.transactions[-n:]))
