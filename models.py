import mysql.connector
from config import Config
import hashlib
from typing import Any


def _dict_rows(rows: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _dict_row(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)

def get_db():
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        port=Config.MYSQL_PORT
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ─── Users ────────────────────────────────────────────────────────────────────

def create_user(full_name, email, phone, address, username, password):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (full_name, email, phone, address, username, password) VALUES (%s,%s,%s,%s,%s,%s)",
            (full_name, email, phone, address, username, hash_password(password))
        )
        db.commit()
        return True, "Registration successful"
    except mysql.connector.IntegrityError:
        return False, "Username or email already exists"
    finally:
        cursor.close(); db.close()

def get_user_by_credentials(username, password):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, hash_password(password))
    )
    user = _dict_row(cursor.fetchone())
    cursor.close(); db.close()
    return user

# ─── Menu ─────────────────────────────────────────────────────────────────────

def get_all_menu():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu ORDER BY category, name")
    items = _dict_rows(cursor.fetchall())
    cursor.close(); db.close()
    return items

def get_menu_item(item_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu WHERE id=%s", (item_id,))
    item = _dict_row(cursor.fetchone())
    cursor.close(); db.close()
    return item


def add_menu_item(name, category, price, description, available=1):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO menu (name, category, price, description, available) VALUES (%s,%s,%s,%s,%s)",
            (name, category, price, description, available)
        )
        db.commit()
        return cursor.lastrowid
    finally:
        cursor.close(); db.close()


def update_menu_item(item_id, name, category, price, description, available):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            UPDATE menu
            SET name=%s, category=%s, price=%s, description=%s, available=%s
            WHERE id=%s
            """,
            (name, category, price, description, available, item_id)
        )
        db.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close(); db.close()

# ─── Tables ───────────────────────────────────────────────────────────────────

def get_all_tables():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tables ORDER BY table_number")
    tables = _dict_rows(cursor.fetchall())
    cursor.close(); db.close()
    return tables

def get_table(table_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tables WHERE id=%s", (table_id,))
    t = _dict_row(cursor.fetchone())
    cursor.close(); db.close()
    return t

def reserve_table(table_id, user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE tables SET status='reserved', reserved_by=%s WHERE id=%s AND status='available'",
        (user_id, table_id)
    )
    db.commit()
    affected = cursor.rowcount
    cursor.close(); db.close()
    return affected > 0

def release_table(table_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE tables SET status='available', reserved_by=NULL WHERE id=%s",
        (table_id,)
    )
    db.commit()
    cursor.close(); db.close()

# ─── Orders ───────────────────────────────────────────────────────────────────

def create_order(user_id, table_id, items, order_type='order_home', payment_method=None, note=None):
    """items: list of {menu_id, quantity}"""
    db = get_db()
    cursor = db.cursor()
    lookup_cursor = db.cursor(dictionary=True)
    try:
        total = 0
        normalized_table_id = int(table_id) if table_id not in (None, "", "null") else None

        if normalized_table_id is not None:
            lookup_cursor.execute(
                "SELECT status, reserved_by FROM tables WHERE id=%s",
                (normalized_table_id,)
            )
            table = _dict_row(lookup_cursor.fetchone())
            if not table:
                return None
            if table['status'] == 'occupied':
                return None
            if table['status'] == 'reserved' and table.get('reserved_by') not in (None, user_id):
                return None

        menu_ids = list({item['menu_id'] for item in items})
        prices: dict[int, Any] = {}
        if menu_ids:
            placeholders = ",".join(["%s"] * len(menu_ids))
            lookup_cursor.execute(
                f"SELECT id, price FROM menu WHERE id IN ({placeholders})",
                tuple(menu_ids)
            )
            prices = {int(row['id']): row['price'] for row in _dict_rows(lookup_cursor.fetchall())}

        for item in items:
            menu_price = prices.get(int(item['menu_id']))
            if menu_price is not None:
                total += menu_price * item['quantity']

        cursor.execute(
            """
            INSERT INTO orders (user_id, table_id, status, total_amount, order_type, payment_method, note)
            VALUES (%s,%s,'pending',%s,%s,%s,%s)
            """,
            (user_id, normalized_table_id, total, order_type, payment_method, note)
        )
        order_id = cursor.lastrowid

        for item in items:
            menu_price = prices.get(int(item['menu_id']))
            if menu_price is not None:
                cursor.execute(
                    "INSERT INTO order_items (order_id, menu_id, quantity, unit_price) VALUES (%s,%s,%s,%s)",
                    (order_id, item['menu_id'], item['quantity'], menu_price)
                )

        if normalized_table_id is not None:
            cursor.execute(
                "UPDATE tables SET status='occupied', reserved_by=%s WHERE id=%s",
                (user_id, normalized_table_id)
            )

        db.commit()
        return order_id
    finally:
        lookup_cursor.close(); cursor.close(); db.close()

def get_orders_by_user(user_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT o.*, u.full_name, u.phone, u.email, u.address,
               t.table_number, t.location AS table_location, t.capacity AS table_capacity,
               t.status AS table_status
        FROM orders o
        JOIN users u ON o.user_id = u.id
        LEFT JOIN tables t ON o.table_id = t.id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC
    """, (user_id,))
    orders = _dict_rows(cursor.fetchall())
    if orders:
        order_ids = [order['id'] for order in orders]
        placeholders = ",".join(["%s"] * len(order_ids))
        cursor.execute(
            f"""
            SELECT oi.*, m.name as item_name
            FROM order_items oi
            JOIN menu m ON oi.menu_id = m.id
            WHERE oi.order_id IN ({placeholders})
            ORDER BY oi.order_id ASC
            """,
            tuple(order_ids)
        )
        grouped_items: dict[int, list[dict[str, Any]]] = {}
        for row in _dict_rows(cursor.fetchall()):
            grouped_items.setdefault(int(row['order_id']), []).append(row)
        for order in orders:
            order['items'] = grouped_items.get(int(order['id']), [])
    cursor.close(); db.close()
    return orders

def get_all_orders():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT o.*, u.full_name, u.phone, u.email, u.address,
               t.table_number, t.location AS table_location, t.capacity AS table_capacity,
               t.status AS table_status
        FROM orders o
        JOIN users u ON o.user_id = u.id
        LEFT JOIN tables t ON o.table_id = t.id
        ORDER BY
          FIELD(o.status,'pending','preparing','ready','completed'),
          o.created_at ASC
    """)
    orders = _dict_rows(cursor.fetchall())
    if orders:
        order_ids = [order['id'] for order in orders]
        placeholders = ",".join(["%s"] * len(order_ids))
        cursor.execute(
            f"""
            SELECT oi.*, m.name as item_name
            FROM order_items oi
            JOIN menu m ON oi.menu_id = m.id
            WHERE oi.order_id IN ({placeholders})
            ORDER BY oi.order_id ASC
            """,
            tuple(order_ids)
        )
        grouped_items: dict[int, list[dict[str, Any]]] = {}
        for row in _dict_rows(cursor.fetchall()):
            grouped_items.setdefault(int(row['order_id']), []).append(row)
        for order in orders:
            order['items'] = grouped_items.get(int(order['id']), [])
    cursor.close(); db.close()
    return orders

def get_order(order_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT o.*, u.full_name, u.phone, u.email, u.address,
               t.table_number, t.location AS table_location, t.capacity AS table_capacity,
               t.status AS table_status
        FROM orders o
        JOIN users u ON o.user_id = u.id
        LEFT JOIN tables t ON o.table_id = t.id
        WHERE o.id = %s
    """, (order_id,))
    order = _dict_row(cursor.fetchone())
    if order:
        cursor.execute("""
            SELECT oi.*, m.name as item_name
            FROM order_items oi
            JOIN menu m ON oi.menu_id = m.id
            WHERE oi.order_id = %s
        """, (order_id,))
        order['items'] = _dict_rows(cursor.fetchall())
    cursor.close(); db.close()
    return order

def update_order_status(order_id, status):
    valid = ['pending', 'preparing', 'ready', 'completed']
    if status not in valid:
        return False
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
    db.commit()
    cursor.close(); db.close()
    return True

def update_order_items(order_id, items):
    """items: list of {menu_id, quantity}"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM order_items WHERE order_id=%s", (order_id,))
    lookup_cursor = db.cursor(dictionary=True)
    total = 0

    menu_ids = list({item['menu_id'] for item in items if item['quantity'] > 0})
    prices: dict[int, Any] = {}
    if menu_ids:
        placeholders = ",".join(["%s"] * len(menu_ids))
        lookup_cursor.execute(
            f"SELECT id, price FROM menu WHERE id IN ({placeholders})",
            tuple(menu_ids)
        )
        prices = {int(row['id']): row['price'] for row in _dict_rows(lookup_cursor.fetchall())}

    for item in items:
        menu_price = prices.get(int(item['menu_id']))
        if menu_price is not None and item['quantity'] > 0:
            cursor.execute(
                "INSERT INTO order_items (order_id, menu_id, quantity, unit_price) VALUES (%s,%s,%s,%s)",
                (order_id, item['menu_id'], item['quantity'], menu_price)
            )
            total += menu_price * item['quantity']
    cursor.execute("UPDATE orders SET total_amount=%s WHERE id=%s", (total, order_id))
    db.commit()
    lookup_cursor.close(); cursor.close(); db.close()


def delete_order(order_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT table_id FROM orders WHERE id=%s", (order_id,))
        order = _dict_row(cursor.fetchone())
        if not order:
            return False

        table_id = order.get('table_id')
        cursor.execute("DELETE FROM orders WHERE id=%s", (order_id,))

        if table_id is not None:
            cursor.execute(
                "UPDATE tables SET status='available', reserved_by=NULL WHERE id=%s",
                (table_id,)
            )

        db.commit()
        return True
    finally:
        cursor.close(); db.close()


def update_table_details(table_id, location, status):
    valid = ['available', 'reserved', 'occupied']
    if status not in valid:
        return False

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE tables SET location=%s, status=%s WHERE id=%s",
            (location, status, table_id)
        )
        db.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close(); db.close()
