# ================= Pseudo Random Number Generator =================
class PseudoRandom:
    def __init__(self, random_state=7):
        self.random_state = random_state

    def next(self):
        self.random_state = (self.random_state * 17 + 43) % 100
        return self.random_state


# ================= Stochastic Product Class =================
class StochasticProduct:
    def __init__(self, name, initial_stock, mean_demand, lead_time):
        self.name = name
        self.stock = initial_stock
        self.mean_demand = mean_demand
        self.lead_time = lead_time
        self.random_no = PseudoRandom()

    def generate_stochastic_demand(self):
        rn = self.random_no.next()

        if rn < 20:
            return self.mean_demand - 1
        elif rn < 70:
            return self.mean_demand
        else:
            return self.mean_demand + 1

    def update_inventory(self):
        demand = self.generate_stochastic_demand()
        self.stock -= demand
        return demand


# ================= Product List =================
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

# Create selected product
name, stock, mean, lead = products[choice]
product = StochasticProduct(name, stock, mean, lead)

demands = []

print("\nProduct:", product.name)
print("\nDay | Demand | Inventory Level")
print("-------------------------------")

for day in range(days):
    d = product.update_inventory()
    demands.append(d)
    print(day + 1, " | ", d, " | ", product.stock)

average_demand = sum(demands) / days

print("\nFinal Inventory Level:", product.stock)
print("Average Daily Demand:", round(average_demand, 2))
