# 🏪 Ration Shop Management System

A full-stack, multi-role Point of Sale (POS) and Inventory Management web application built with **Python (Flask)** and **MySQL**. 

Originally designed as a DBMS project, it has been completely re-architected into a modern business solution. It demonstrates secure authentication, dynamic inventory management, employee tracking, and real-time analytics.

## 🚀 Key Features
*   **Role-Based Access Control:** Separate dashboards for Shop Owners and Employees.
*   **Employee Onboarding:** Employees register, but require Owner approval to access the system.
*   **Dynamic Inventory:** Owners can add items, update prices in real-time, and receive Low Stock Alerts.
*   **Sales Terminal (POS):** Employees build a multi-item cart, auto-calculate totals, and simulate a QR payment checkout.
*   **Automated Receipts:** Generates printable digital receipts for every transaction.
*   **Staff Management:** Owners can suspend or reactivate employee accounts.
*   **Analytics & Reports:** Interactive Chart.js graphs showing top-selling items and employee performance.
*   **Password Reset:** Secure OTP verification flow for forgotten passwords.

## 🛠️ Tech Stack
*   **Backend:** Python, Flask
*   **Database:** MySQL
*   **Frontend:** HTML5, Jinja2, CSS3, Chart.js
*   **Security:** Parameterized SQL queries, session management.

## 💻 How to Run Locally
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your DB credentials (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).
4. Import the provided SQL schema into MySQL.
5. Run the app: `python app.py`

## 🔑 Default Credentials
*   **Owner:** `owner` / `owner123`
