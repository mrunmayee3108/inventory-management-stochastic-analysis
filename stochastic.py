# ================= Pseudo Random Number Generator =================
class PseudoRandom:
    def __init__(self, seed=7):
        self.seed = seed

    def next(self):
        # Linear Congruential Generator (0–99)
        self.seed = (self.seed * 17 + 43) % 100
        return self.seed


# ================= Base Product Class =================
class StochasticProduct:
    def __init__(self, name, initial_stock, mean_demand, lead_time):
        self.name = name
        self.stock = initial_stock
        self.mean_demand = mean_demand
        self.lead_time = lead_time
        self.history = []
        self.prng = PseudoRandom()

    def generate_stochastic_demand(self):
        """
        Simple stochastic (rule-based) demand model
        """
        rn = self.prng.next()

        if rn < 20:
            return max(1, self.mean_demand - 1)
        elif rn < 70:
            return self.mean_demand
        else:
            return self.mean_demand + 1

    def calculate_safety_stock(self):
        """
        Approximate safety stock without math library
        """
        return (self.mean_demand * self.lead_time) // 2

    def update_inventory(self):
        demand = self.generate_stochastic_demand()
        self.stock -= demand
        self.history.append(self.stock)
        return demand


# ================= Monte Carlo Product Class =================
class MonteCarloProduct(StochasticProduct):
    def generate_stochastic_demand(self):
        """
        Monte Carlo simulation using probability ranges
        """
        rn = self.prng.next()

        if rn <= 9:
            return 1
        elif rn <= 29:
            return 2
        elif rn <= 69:
            return 3
        elif rn <= 89:
            return 4
        else:
            return 5


# ================= Poisson Product Class =================
class PoissonProduct(StochasticProduct):
    def generate_stochastic_demand(self):
        """
        Poisson demand using Knuth's algorithm (no libraries)
        """
        # Approximate e^-lambda
        L = 1
        for _ in range(self.mean_demand):
            L *= 0.37   # approx of e^-1

        k = 0
        p = 1

        while p > L:
            k += 1
            p *= self.prng.next() / 100

        return max(1, k - 1)


# ================= Main Simulation =================
products = {
    1: ("Gaming Laptop", 50, 3, 5),
    2: ("Smartphone", 100, 6, 4),
    3: ("Headphones", 200, 10, 2)
}

print("\nINVENTORY MANAGEMENT SIMULATION")
print("----------------------------------")
print("Select Product:")

for key in products:
    print(key, "->", products[key][0])

choice = int(input("\nEnter product number: "))
days = int(input("Enter number of simulation days: "))

print("\nSelect Demand Model:")
print("1 -> Simple Stochastic Model")
print("2 -> Monte Carlo Model")
print("3 -> Poisson Distribution Model")

model = int(input("Enter choice: "))

name, stock, mean, lead = products[choice]

if model == 1:
    product = StochasticProduct(name, stock, mean, lead)
    model_name = "Simple Stochastic Model"

elif model == 2:
    product = MonteCarloProduct(name, stock, mean, lead)
    model_name = "Monte Carlo Model"

else:
    product = PoissonProduct(name, stock, mean, lead)
    model_name = "Poisson Distribution Model"

demands = []

print("\nProduct:", product.name)
print("Model Used:", model_name)
print("\nDay | Demand | Inventory Level")
print("-------------------------------")

for day in range(days):
    d = product.update_inventory()
    demands.append(d)
    print(day + 1, " | ", d, " | ", product.stock)

average_demand = sum(demands) / days

print("\nFinal Inventory Level:", product.stock)
print("Average Daily Demand:", average_demand)
print("Safety Stock Level:", product.calculate_safety_stock())
