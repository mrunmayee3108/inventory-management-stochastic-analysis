import time
class RandomEngine:
    A = 1664525
    C = 1013904223
    M = 2 ** 32

    def __init__(self, seed=None):
        self.state = seed if seed is not None else int(time.time() * 1000) % self.M

    def rand_float(self):
        self.state = (self.A * self.state + self.C) % self.M
        return self.state/self.M

    def rand_int(self, lo, hi):
        return lo + int(self.rand_float() * (hi - lo + 1))

    def rand_normal(self, mean, std):
        u1 = max(0.00001, self.rand_float())
        u2 = self.rand_float()
        z  = self._sqrt(-2.0 * self._ln(u1)) * self._cos(2.0 * 3.14159265 * u2)
        return max(0.0, mean + std * z)

    def _sqrt(self, x):
        if x <= 0: return 0.0
        g = x / 2.0
        for _ in range(40):
            g = (g + x / g) / 2.0
        return g

    def _ln(self, x):
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

    def _cos(self, x):
        PI = 3.14159265
        while x > PI: x -= 2 * PI
        while x < -PI: x += 2 * PI
        s, t, sign = 0.0, 1.0, 1.0
        for n in range(1, 14):
            s += sign * t
            t *= x * x / ((2*n) * (2*n - 1))
            sign *= -1.0
        return s

class MonteCarloSimulator:
    def __init__(self, product, num_runs=300, days=60):
        self.product = product
        self.num_runs = num_runs
        self.days = days
        self.profits = []
        self.services = []
        self.wastes = []

    def run(self, drought=False):
        self.profits = []
        self.services = []
        self.wastes = []
        p = self.product

        for run_no in range(self.num_runs):
            rng = RandomEngine(seed=run_no * 7919 + 1)
            stock = p.reorder_point  
            age = 0
            total_profit = 0.0
            total_sold = 0
            total_demand = 0
            total_spoiled = 0
            total_received = stock

            for day in range(1, self.days + 1):
                if drought:
                    supply = int(rng.rand_normal(p.avg_demand * p.drought_factor, p.demand_std * p.drought_factor))
                else:
                    supply = int(rng.rand_normal(p.avg_demand, p.demand_std))
                supply = max(0, supply)
                stock += supply
                total_received += supply

                demand = int(rng.rand_normal(p.avg_demand, p.demand_std))
                if day % 7 in (5, 6):
                    demand = int(demand * 1.3)
                demand = max(0, demand)
                total_demand += demand

                age += 1
                spoiled = 0
                if age >= p.shelf_life:
                    spoiled = stock
                    total_spoiled += spoiled
                    stock = 0
                    age = 0

                sold = min(stock, demand)
                stockout = max(0, demand - stock)
                stock -= sold
                total_sold += sold

                if stock < p.reorder_point:
                    stock += p.reorder_qty

                profit = (sold * p.sale_price - spoiled * p.waste_cost - stockout * p.stockout_cost)
                total_profit += profit

            svc = (total_sold / total_demand * 100) if total_demand else 100.0
            wst = (total_spoiled / total_received * 100) if total_received else 0.0
            self.profits.append(round(total_profit, 2))
            self.services.append(round(svc, 1))
            self.wastes.append(round(wst, 1))

    def summary(self):
        def avg(lst): return round(sum(lst) / len(lst), 2) if lst else 0
        def std(lst):
            if not lst: return 0
            m = avg(lst)
            rng = RandomEngine()
            return round(rng._sqrt(sum((x-m)**2 for x in lst) / len(lst)), 2)
        return {
            "profits":  self.profits,
            "services": self.services,
            "wastes":   self.wastes,
            "avg_profit":  avg(self.profits),
            "std_profit":  std(self.profits),
            "best":        round(max(self.profits), 2),
            "worst":       round(min(self.profits), 2),
            "avg_service": avg(self.services),
            "avg_waste":   avg(self.wastes),
        }

    def safety_stock(self):
        rng = RandomEngine()
        return round(1.65 * self.product.demand_std * rng._sqrt(2))
