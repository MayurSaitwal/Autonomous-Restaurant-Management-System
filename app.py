from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from config import Config
from models import (
    create_user, get_user_by_credentials,
    get_all_menu, get_menu_item,
    add_menu_item, update_menu_item,
    get_all_tables, get_table, reserve_table, release_table,
    create_order, get_orders_by_user, get_all_orders, get_order,
    update_order_status, update_order_items, delete_order, update_table_details
)
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# ─── Auth Decorators ──────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('customer_login'))
        return f(*args, **kwargs)
    return decorated

def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_staff'):
            flash('Staff access required.', 'warning')
            return redirect(url_for('staff_login'))
        return f(*args, **kwargs)
    return decorated

# ─── Root ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('customer_login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        success, msg = create_user(
            request.form['full_name'],
            request.form['email'],
            request.form['phone'],
            request.form.get('address', '').strip(),
            request.form['username'],
            request.form['password']
        )
        if success:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('customer_login'))
        flash(msg, 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        user = get_user_by_credentials(request.form['username'], request.form['password'])
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['username'] = user['username']
            return redirect(url_for('customer_dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('customer_login'))

# ─── Customer Dashboard ───────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def customer_dashboard():
    return render_template('customer_dashboard.html')

@app.route('/dashboard_data')
@login_required
def dashboard_data():
    menu = get_all_menu()
    tables = get_all_tables()
    orders = get_orders_by_user(session['user_id'])
    categories = sorted(set(item['category'] for item in menu))
    return jsonify({
        'menu': menu,
        'tables': tables,
        'orders': orders,
        'categories': categories,
        'user_name': session.get('user_name', ''),
    })

@app.route('/reserve_table', methods=['POST'])
@login_required
def reserve_table_route():
    table_id = request.form.get('table_id')
    if reserve_table(table_id, session['user_id']):
        flash('Table reserved successfully!', 'success')
    else:
        flash('Table is not available.', 'error')
    return redirect(url_for('customer_dashboard'))

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    data = request.get_json()
    order_type = data.get('order_type', 'order_home')
    payment_method = data.get('payment_method') if order_type == 'order_home' else None
    table_id = data.get('table_id') if order_type == 'dine_in' else None
    note = (data.get('note') or '').strip() or None
    items = data.get('items', [])
    if not items:
        return jsonify({'success': False, 'message': 'No items selected.'})
    if order_type not in ('dine_in', 'order_home'):
        return jsonify({'success': False, 'message': 'Invalid order type.'})
    if order_type == 'order_home' and payment_method != 'cod':
        return jsonify({'success': False, 'message': 'Please choose Cash on Delivery for home orders.'})
    if order_type == 'dine_in' and not table_id:
        return jsonify({'success': False, 'message': 'Please select a table for dine in.'})

    order_id = create_order(session['user_id'], table_id, items, order_type, payment_method, note)
    if not order_id:
        return jsonify({'success': False, 'message': 'Selected table is not available right now. Choose another table.'})
    return jsonify({'success': True, 'order_id': order_id, 'message': 'Order placed successfully!'})

@app.route('/my_orders')
@login_required
def my_orders():
    orders = get_orders_by_user(session['user_id'])
    return jsonify(orders)

# ─── Staff Auth ───────────────────────────────────────────────────────────────

@app.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        if (request.form['username'] == Config.STAFF_USERNAME and
                request.form['password'] == Config.STAFF_PASSWORD):
            session['is_staff'] = True
            session['staff_name'] = 'Staff'
            return redirect(url_for('staff_dashboard'))
        flash('Invalid staff credentials.', 'error')
    return render_template('staff_login.html')

@app.route('/staff/logout')
def staff_logout():
    session.clear()
    return redirect(url_for('staff_login'))

# ─── Staff Dashboard ──────────────────────────────────────────────────────────

@app.route('/staff/dashboard')
@staff_required
def staff_dashboard():
    orders = get_all_orders()
    menu = get_all_menu()
    tables = get_all_tables()
    return render_template('staff_dashboard.html', orders=orders, menu=menu, tables=tables)

@app.route('/staff/update_status', methods=['POST'])
@staff_required
def update_status():
    data = request.get_json()
    success = update_order_status(data.get('order_id'), data.get('status'))
    return jsonify({'success': success})

@app.route('/staff/update_order', methods=['POST'])
@staff_required
def update_order():
    data = request.get_json()
    order_id = data.get('order_id')
    items = data.get('items', [])
    update_order_items(order_id, items)
    order = get_order(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found.'}), 404
    return jsonify({'success': True, 'total': float(order['total_amount'])})

@app.route('/staff/delete_order', methods=['POST'])
@staff_required
def remove_order():
    data = request.get_json()
    success = delete_order(data.get('order_id'))
    return jsonify({'success': success})

@app.route('/staff/orders_json')
@staff_required
def staff_orders_json():
    orders = get_all_orders()
    result = []
    for o in orders:
        od = {k: (str(v) if hasattr(v, 'isoformat') else v) for k, v in o.items() if k != 'items'}
        od['items'] = o.get('items', [])
        result.append(od)
    return jsonify(result)


@app.route('/staff/tables_json')
@staff_required
def staff_tables_json():
    return jsonify(get_all_tables())


@app.route('/staff/update_table', methods=['POST'])
@staff_required
def staff_update_table():
    data = request.get_json()
    table_id = data.get('table_id')
    location = (data.get('location') or '').strip()
    status = data.get('status')

    if not table_id or not location:
        return jsonify({'success': False, 'message': 'Table, location and status are required.'})

    success = update_table_details(table_id, location, status)
    if not success:
        return jsonify({'success': False, 'message': 'Unable to update table.'})
    return jsonify({'success': True})


@app.route('/staff/menu_json')
@staff_required
def staff_menu_json():
    return jsonify(get_all_menu())


@app.route('/staff/update_menu_item', methods=['POST'])
@staff_required
def staff_update_menu_item():
    data = request.get_json()
    item_id = data.get('item_id')
    name = (data.get('name') or '').strip()
    category = (data.get('category') or '').strip()
    description = (data.get('description') or '').strip()
    price = data.get('price')
    available = 1 if data.get('available') else 0

    if not item_id or not name or not category:
        return jsonify({'success': False, 'message': 'Name and category are required.'})
    try:
        price = float(price)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid price.'})
    if price <= 0:
        return jsonify({'success': False, 'message': 'Price must be greater than zero.'})

    success = update_menu_item(item_id, name, category, price, description, available)
    if not success:
        return jsonify({'success': False, 'message': 'Unable to update menu item.'})
    return jsonify({'success': True})


@app.route('/staff/add_menu_item', methods=['POST'])
@staff_required
def staff_add_menu_item():
    data = request.get_json()
    name = (data.get('name') or '').strip()
    category = (data.get('category') or '').strip()
    description = (data.get('description') or '').strip()
    price = data.get('price')
    available = 1 if data.get('available', True) else 0

    if not name or not category:
        return jsonify({'success': False, 'message': 'Name and category are required.'})
    try:
        price = float(price)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid price.'})
    if price <= 0:
        return jsonify({'success': False, 'message': 'Price must be greater than zero.'})

    item_id = add_menu_item(name, category, price, description, available)
    return jsonify({'success': True, 'item_id': item_id})

if __name__ == '__main__':
    app.run(debug=True)
