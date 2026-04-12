
# Autonomous-Restaurant-Management-System
# 🍽 Saveur — Restaurant Management System


---

## Project Structure

```
restaurant_system/
├── app.py              # Main Flask application & all routes
├── config.py           # Configuration (DB credentials, secret key)
├── models.py           # All database helper functions
├── requirements.txt    # Python dependencies
├── database.sql        # MySQL schema + seed data
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── staff_login.html
│   ├── customer_dashboard.html
│   └── staff_dashboard.html
└── static/
    └── css/
        └── style.css
```

---

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up MySQL Database

Make sure MySQL is running, then:

```bash
mysql -u root -p < database.sql
```

Or open MySQL Workbench / phpMyAdmin and run the contents of `database.sql`.

This creates:
- The `restaurant_db` database
- All 5 tables: `users`, `menu`, `tables`, `orders`, `order_items`
- Seed data: 10 tables + 20 menu items

### 3. Configure Database Credentials

Open `config.py` and update if needed:

```python
MYSQL_HOST     = 'localhost'
MYSQL_USER     = 'root'
MYSQL_PASSWORD = ''        # ← your MySQL password
MYSQL_DATABASE = 'restaurant_db'
MYSQL_PORT     = 3306
```

### 4. Run the Application

```bash
python app.py
```

Open your browser at: **http://127.0.0.1:5000**

---

## Login Credentials

| Role     | Username | Password |
|----------|----------|----------|
| Staff    | staff    | admin123 |
| Customer | Register first via /register |

---

## Features Summary

### Customer
- Register & Login
- Browse menu with category filters
- Add items to cart with quantity controls
- Select a table and reserve it
- Place orders
- Track order status (Pending → Preparing → Ready → Completed)
- Auto-refresh order status every 30 seconds

### Staff
- Login with default credentials
- View all orders with customer details
- Filter orders by status (Pending / Preparing / Ready / Completed)
- Live stats (count per status)
- Update order status with dropdown
- Edit order items and quantities via modal
- Auto-refresh every 20 seconds

---

## Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Backend    | Python Flask 3.0        |
| Database   | MySQL                   |
| Connector  | mysql-connector-python  |
| Auth       | Flask session management |
| Frontend   | HTML5 + CSS3 + JavaScript |
| Fonts      | Playfair Display + DM Sans (Google Fonts) |
>>>>>>> 5339aaf (Initial commit)
