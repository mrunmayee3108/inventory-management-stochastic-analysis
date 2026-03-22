class Product:
    def __init__(self, name, category, unit, stock, reorder_point):
        self.name = name
        self.category = category
        self.unit = unit
        self.current_stock = stock
        self.reorder_point = reorder_point

    def needs_reorder(self):
        return self.current_stock < self.reorder_point

    def add_stock(self, qty):
        self.current_stock += qty

    def remove_stock(self, qty):
        sold = min(self.current_stock, qty)
        self.current_stock -= sold
        return sold

    def is_expired(self):
        return False

    def __str__(self):
        return f"{self.name} — {self.current_stock} {self.unit}"

class PerishableProduct(Product):
    def __init__(self, name, category, unit,
                 stock, reorder_point, reorder_qty,
                 shelf_life, sale_price, avg_demand):

        super().__init__(name, category, unit, stock, reorder_point)

        self.reorder_qty = reorder_qty
        self.shelf_life = shelf_life      
        self.sale_price = sale_price
        self.avg_demand = avg_demand
        self.age_days = 0              
        self.demand_std = avg_demand * 0.20
        self.waste_cost = round(sale_price * 0.30, 2)
        self.stockout_cost = round(sale_price * 0.60, 2)
        self.drought_factor = 0.30

    def is_expired(self):
        return self.age_days >= self.shelf_life

    def days_left(self):
        return max(0, self.shelf_life - self.age_days)

    def critical_ratio(self):
        return round(self.stockout_cost / (self.stockout_cost + self.waste_cost), 3)

def default_products():
    return [
        # Arguments: name, category, unit, stock, reorder_point, reorder_qty, shelf_life, sale_price, avg_demand
        PerishableProduct("Milk", "Dairy", "L", 140, 50, 100, 7, 35, 120),
        PerishableProduct("Strawberries", "Fruit", "kg", 22, 15, 40, 3, 80, 60),
        PerishableProduct("Leafy Greens", "Vegetable", "kg", 60, 30, 60, 4, 45, 80),
        PerishableProduct("Bread", "Bakery", "pcs", 38, 20, 50, 2, 25, 50),
        PerishableProduct("Tomatoes", "Vegetable", "kg", 85, 30, 60, 5, 35, 90),
        PerishableProduct("Mangoes", "Fruit", "kg", 55, 20, 50, 6, 70, 60),
    ]
