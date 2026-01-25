import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import random

class StochasticProduct:
    def __init__(self, name, initial_stock, mean_demand, lead_time):
        self.name = name
        self.stock = initial_stock
        self.mean_demand = mean_demand
        self.lead_time = lead_time
        self.history = []
        
    def generate_stochastic_demand(self):
        """Encapsulation: The object decides its own demand based on Poisson"""
        return np.random.poisson(self.mean_demand)

    def calculate_safety_stock(self, service_level_factor=1.645):
        """
        Stochastic Analysis: Z * sqrt(Lead Time) * StdDev
        For Poisson, StdDev = sqrt(mean_demand)
        """
        std_dev = np.sqrt(self.mean_demand)
        safety_stock = service_level_factor * std_dev * np.sqrt(self.lead_time)
        return round(safety_stock)

    def update_inventory(self):
        demand = self.generate_stochastic_demand()
        self.stock -= demand
        self.history.append(self.stock)
        return demand


MC_TABLE = [
    {"demand": 1, "start": 0,  "end": 9},
    {"demand": 2, "start": 10, "end": 29},
    {"demand": 3, "start": 30, "end": 69},
    {"demand": 4, "start": 70, "end": 89},
    {"demand": 5, "start": 90, "end": 99},
]

class MonteCarloProduct(StochasticProduct):
    def generate_stochastic_demand(self):
        rn = random.randint(0, 99)
        for row in MC_TABLE:
            if row["start"] <= rn <= row["end"]:
                return row["demand"]
            
PRODUCTS = {
    "Gaming Laptop": {"stock": 50, "mean": 3, "lead": 5},
    "Smartphone": {"stock": 100, "mean": 6, "lead": 4},
    "Headphones": {"stock": 200, "mean": 10, "lead": 2}
}

st.title("📦 Inventory Simulation")
st.sidebar.header("Simulation Settings")

model = st.sidebar.radio("Demand Model", ["Poisson", "Monte Carlo"])
product_name = st.sidebar.selectbox("Product", PRODUCTS.keys())
days = st.sidebar.slider("Simulation Days", 5, 30, 14)

params = PRODUCTS[product_name]

if st.button("Run Simulation"):

    if model == "Poisson":
        st.subheader("Poisson based simulation")
        product = StochasticProduct(
            product_name, params["stock"], params["mean"], params["lead"]
        )
    else:
        st.subheader("Monte Carlo based simulation")
        product = MonteCarloProduct(
            product_name, params["stock"], params["mean"], params["lead"]
        )

    demands = []
    for _ in range(days):
        demands.append(product.update_inventory())

    st.subheader(f"{product.name} – {model} Model")

    col1, col2, col3 = st.columns(3)
    col1.metric("Final Stock", product.stock)
    col2.metric("Avg Demand", round(np.mean(demands), 2))
    col3.metric("Safety Stock", product.calculate_safety_stock())

    fig, ax = plt.subplots()
    ax.plot(product.history, marker="o")
    ax.axhline(0, linestyle="--")
    ax.set_xlabel("Days")
    ax.set_ylabel("Inventory Level")
    st.pyplot(fig)

    st.table({
        "Day": list(range(1, days + 1)),
        "Demand": demands,
        "Inventory": product.history
    })
