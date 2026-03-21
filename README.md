# 🌿 AgriStock — Stochastic Perishable Inventory Management System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python"/>
  <img src="https://img.shields.io/badge/GUI-Tkinter-green?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Visualization-Matplotlib-orange?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Model-Monte%20Carlo-red?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge"/>
</p>

## 📌 Project Overview

**AgriStock** is a **stochastic inventory management system** built for **perishable goods** like fruits, vegetables, dairy, and bakery items.

It combines:

* 📦 Inventory Management
* ⏳ Spoilage Tracking
* 🎲 Monte Carlo Simulation
* 📊 Data Visualization

to help businesses **optimize stock decisions under uncertainty**.


## 🎯 Objectives

* Reduce **wastage due to spoilage**
* Prevent **stockouts**
* Apply **probabilistic decision-making**
* Provide **data-driven insights**
* Simulate **real-world demand variability**


## 🧠 Core Concepts

* 🧩 Object-Oriented Programming (OOP)
* 🧠 Abstraction (GUI ↔ Backend separation)
* 🎲 Monte Carlo Simulation
* 📐 Newsvendor Model (Critical Ratio)
* 📊 Safety Stock Calculation


## 🛠️ Tech Stack

| Category      | Technology  |
| ------------- | ----------- |
| Language      | Python      |
| GUI           | Tkinter     |
| Visualization | Matplotlib  |
| Architecture  | OOP         |
| Simulation    | Monte Carlo |


## 📸 Demo Screenshots
<img width="1268" height="787" alt="image" src="https://github.com/user-attachments/assets/1bf89735-788b-4a7f-b73b-bfc8a9cc9ce6" />
<img width="1919" height="1022" alt="image" src="https://github.com/user-attachments/assets/f9966cef-ce36-4c16-836a-7633560aa2bb" />
<img width="1918" height="1015" alt="image" src="https://github.com/user-attachments/assets/54ede203-f2a7-4bd8-a67c-f51a17450361" />
<img width="1919" height="1020" alt="image" src="https://github.com/user-attachments/assets/0aacdbab-9d53-4778-8d00-4c656ff73abe" />
<img width="1919" height="1023" alt="image" src="https://github.com/user-attachments/assets/3299d521-3483-419a-9585-71cbc31b4285" />


## ✨ Features

### 📊 Dashboard

* KPI cards (Stock, Low Stock, Expiring Items)
* Stock visualization
* Alerts system
* Transaction logs


### 📦 Manage Products

* Add & delete products
* Auto-calculated:

  * Waste cost
  * Stockout cost
  * Critical Ratio
* Record:

  * Deliveries 📦
  * Sales 🛒


### 🎲 Simulation (Core Feature)

* Monte Carlo simulation
* Metrics:

  * Profit 💰
  * Service Level 📈
  * Waste Rate 🗑️
* Histograms for analysis
* 🌵 Drought scenario simulation


### 📈 Reports

* Demand vs Reorder Point
* Critical Ratio comparison
* Profit distribution charts


### 🗑️ Spoilage Tracker

* Expiry monitoring
* Freshness visualization
* Advance-day simulation
* Auto removal of expired stock


## 📂 Project Structure

```bash
final_inventory/
│
├── app.py          # Main GUI application
├── inventory.py    # Inventory logic
├── product.py      # Perishable product model
├── stochastic.py   # Monte Carlo simulation
```


## ⚙️ How to Run

### 1️⃣ Clone Repository

```bash
git clone https://github.com/mrunmayee3108/inventory-management-stochastic-analysis.git
cd inventory-management-stochastic-analysis/final_inventory
```

### 2️⃣ Install Dependencies

```bash
pip install matplotlib
```

### 3️⃣ Run Application

```bash
python app.py
```


## 📊 Workflow

1. Add products (Apples 🍎, Milk 🥛, Bread 🍞)
2. Record sales & deliveries
3. Run simulation 🎲
4. Analyze:

   * Profit trends
   * Waste levels
   * Service levels
5. Optimize decisions 📈


## 📐 Important Formulas

### 🔹 Critical Ratio

```
CR = Cu / (Cu + Co)
```

### 🔹 Safety Stock

```
SS = Z × σ × √(Lead Time)
```


## 🚀 Future Enhancements

* 🔄 Database integration (SQLite / PostgreSQL)
* 🌐 Web version (React + Flask)
* 🤖 ML-based demand forecasting
* 🌦️ Weather API integration
* 🏭 Multi-warehouse support


## 👩‍💻 Contributors

- **Mrunmayee Potdar** — @mrunmayee3108  
- **Ekta Sawant** — @EktaSawant46  
- **Mahi Pendkalkar** — @Mahii0107  
- **Siddhi Thakur** — @Siddhi-S-Thakur  

## 💬 Support

If you liked this project:

* ⭐ Star the repo
* 🍴 Fork it
* 🤝 Contribute
