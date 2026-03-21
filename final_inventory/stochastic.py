# ================================================================
# stochastic.py  —  Random Engine + Monte Carlo Simulator
# ================================================================
# NO external libraries. Random numbers built from scratch.
#
# Classes:
#   RandomEngine        : LCG random number generator
#   MonteCarloSimulator : runs N simulations, collects statistics
# ================================================================

import time


class RandomEngine:
    """
    Our own random number generator (no import random).

    Algorithm: Linear Congruential Generator (LCG)
    Formula  : next = (A × state + C) % M
    Same formula Python's own random module uses internally.

    For Normal (bell-curve) numbers we use Box-Muller Transform:
        z = sqrt(−2 × ln(u1)) × cos(2π × u2)
    We build sqrt, ln, cos ourselves too.
    """

    A = 1664525
    C = 1013904223
    M = 2 ** 32

    def __init__(self, seed=None):
        self.state = seed if seed is not None else int(time.time() * 1000) % self.M

    def rand_float(self):
        """Random float between 0.0 and 1.0"""
        self.state = (self.A * self.state + self.C) % self.M
        return self.state / self.M

    def rand_int(self, lo, hi):
        """Random integer between lo and hi inclusive."""
        return lo + int(self.rand_float() * (hi - lo + 1))

    def rand_normal(self, mean, std):
        """
        Random number from a Normal (bell-curve) distribution.
        Box-Muller Transform — converts two uniform random
        numbers into one Gaussian random number.
        """
        u1 = max(0.00001, self.rand_float())
        u2 = self.rand_float()
        z  = self._sqrt(-2.0 * self._ln(u1)) * self._cos(2.0 * 3.14159265 * u2)
        return max(0.0, mean + std * z)

    # ── Math helpers (no import math) ────────────────────────────

    def _sqrt(self, x):
        """Square root via Newton-Raphson: g = (g + x/g) / 2"""
        if x <= 0: return 0.0
        g = x / 2.0
        for _ in range(40):
            g = (g + x / g) / 2.0
        return g

    def _ln(self, x):
        """Natural log via series expansion."""
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
        """Cosine via Taylor series."""
        PI = 3.14159265
        while x >  PI: x -= 2 * PI
        while x < -PI: x += 2 * PI
        s, t, sign = 0.0, 1.0, 1.0
        for n in range(1, 14):
            s    += sign * t
            t    *= x * x / ((2*n) * (2*n - 1))
            sign *= -1.0
        return s


# ────────────────────────────────────────────────────────────────

class MonteCarloSimulator:
    """
    Runs the inventory simulation N times with different random seeds.
    Each run gives a different profit because demand is random.
    Together, all runs show the RANGE and RISK of the inventory policy.

    Each simulated day:
      1. Supply arrives from farm  (Normal random, less during drought)
      2. Customer demand arrives   (Normal random, +30% on weekends)
      3. Spoilage check            (stock expires after shelf_life days)
      4. Sell                      (sell as much as possible)
      5. Reorder if needed         (if stock < reorder_point)
      6. Calculate today's profit
    """

    def __init__(self, product, num_runs=300, days=60):
        self.product  = product
        self.num_runs = num_runs
        self.days     = days

        # Results filled after run()
        self.profits  = []
        self.services = []
        self.wastes   = []

    def run(self, drought=False):
        """Run num_runs independent simulations."""
        self.profits  = []
        self.services = []
        self.wastes   = []
        p = self.product

        for run_no in range(self.num_runs):
            rng = RandomEngine(seed=run_no * 7919 + 1)

            stock          = p.reorder_point   # start with safety stock
            age            = 0
            total_profit   = 0.0
            total_sold     = 0
            total_demand   = 0
            total_spoiled  = 0
            total_received = stock

            for day in range(1, self.days + 1):

                # STEP 1 — Supply
                if drought:
                    supply = int(rng.rand_normal(
                        p.avg_demand * p.drought_factor,
                        p.demand_std * p.drought_factor))
                else:
                    supply = int(rng.rand_normal(p.avg_demand, p.demand_std))
                supply          = max(0, supply)
                stock          += supply
                total_received += supply

                # STEP 2 — Demand (30% more on weekends)
                demand = int(rng.rand_normal(p.avg_demand, p.demand_std))
                if day % 7 in (5, 6):
                    demand = int(demand * 1.3)
                demand        = max(0, demand)
                total_demand += demand

                # STEP 3 — Spoilage
                age    += 1
                spoiled = 0
                if age >= p.shelf_life:
                    spoiled        = stock
                    total_spoiled += spoiled
                    stock          = 0
                    age            = 0

                # STEP 4 — Sell
                sold      = min(stock, demand)
                stockout  = max(0, demand - stock)
                stock    -= sold
                total_sold += sold

                # STEP 5 — Reorder
                if stock < p.reorder_point:
                    stock += p.reorder_qty

                # STEP 6 — Profit
                profit       = (sold    * p.sale_price
                              - spoiled * p.waste_cost
                              - stockout* p.stockout_cost)
                total_profit += profit

            # KPIs for this run
            svc = (total_sold / total_demand * 100)   if total_demand   else 100.0
            wst = (total_spoiled / total_received * 100) if total_received else 0.0
            self.profits.append(round(total_profit, 2))
            self.services.append(round(svc, 1))
            self.wastes.append(round(wst, 1))

    def summary(self):
        """Statistics from all runs."""
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
        """
        Recommended Safety Stock = Z × σ × √(Lead Time)
        Z = 1.65  (for 95% service level)
        σ = demand standard deviation
        Lead Time = 2 days assumed
        """
        rng = RandomEngine()
        return round(1.65 * self.product.demand_std * rng._sqrt(2))
