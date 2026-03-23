from datetime import datetime
from product import default_products, PerishableProduct

class Inventory:
    def __init__(self):
        self.products     = default_products()
        self.transactions = []

    def get(self, name):
        for p in self.products:
            if p.name == name:
                return p
        return None

    def add_stock(self, name, qty):
        p = self.get(name)
        if p:
            p.add_stock(qty)
            p.age_days = 0
            self._log(name, "DELIVERY", qty, "Stock received")

    def sell_stock(self, name, qty):
        p = self.get(name)
        if p:
            sold = p.remove_stock(qty)
            self._log(name, "SALE", sold, "Sold to customer")
            return sold
        return 0

    def add_product(self, product):
        self.products.append(product)
        self._log(product.name, "ADDED", product.current_stock, "New product added")

    def delete_product(self, name):
        p = self.get(name)
        if p:
            self.products.remove(p)
            self._log(name, "DELETED", 0, "Product removed")
            return True
        return False

    def advance_day(self):
        expired = []
        for p in self.products:
            p.age_days += 1
            if p.is_expired() and p.current_stock > 0:
                expired.append((p.name, p.current_stock, p.unit))
                self._log(p.name, "SPOILED", p.current_stock, "Expired and removed")
                p.current_stock = 0
                p.age_days = 0
        return expired

    def low_stock(self):
        return [p for p in self.products if p.needs_reorder()]

    def expiring_soon(self):
        return [p for p in self.products if 0 < p.days_left() <= 3]

    def _log(self, name, action, qty, note):
        self.transactions.append({
            "time": datetime.now().strftime("%d %b  %H:%M"),
            "product": name,
            "action": action,
            "qty": qty,
            "note": note,
        })

    def recent_log(self, n=15):
        return list(reversed(self.transactions[-n:]))
