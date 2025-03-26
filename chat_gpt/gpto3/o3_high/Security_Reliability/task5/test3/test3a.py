from flask import Flask, request, session, g, redirect, url_for, render_template_string, abort
import sqlite3, os, secrets

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure random key for sessions and CSRF

DATABASE = 'ecommerce.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    db = get_db()
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("DROP TABLE IF EXISTS products")
    # Create users table with an "is_admin" flag
    
    db.execute('''
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        is_admin INTEGER DEFAULT 0
      )
    ''')
    # Create products table
    db.execute('''
      CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
      )
    ''')
    db.commit()
    # Insert a test admin user if one doesn't already exist
    cur = db.execute("SELECT * FROM users WHERE username = ?", ('admin',))
    if cur.fetchone() is None:
        db.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ('admin', 1))
        db.commit()

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cur.fetchone()

# Decorator to ensure the current user is an admin
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user is None or user['is_admin'] == 0:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Simple CSRF token generation and validation
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

def validate_csrf_token(token):
    return token == session.get('_csrf_token')

@app.before_request
def auto_login():
    # For demonstration purposes, auto‑login as our test admin if not already logged in
    if 'user_id' not in session:
        db = get_db()
        cur = db.execute("SELECT id FROM users WHERE username = ?", ('admin',))
        user = cur.fetchone()
        if user:
            session['user_id'] = user['id']

# Make the CSRF token available in all templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf_token())

# Admin panel: List products, add new ones, and provide edit/delete links.
@app.route('/admin', methods=['GET'])
@admin_required
def admin_panel():
    db = get_db()
    cur = db.execute("SELECT * FROM products")
    products = cur.fetchall()
    template = '''
    <h1>Admin Panel - Manage Products</h1>
    <h2>Add New Product</h2>
    <form method="POST" action="{{ url_for('add_product') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        Name: <input type="text" name="name"><br>
        Description: <textarea name="description"></textarea><br>
        Price: <input type="number" step="0.01" name="price"><br>
        <input type="submit" value="Add Product">
    </form>
    <h2>Existing Products</h2>
    <ul>
    {% for product in products %}
        <li>
            <strong>{{ product['name'] }}</strong> - ${{ product['price'] }}<br>
            {{ product['description']|e }}<br>
            <a href="{{ url_for('edit_product', product_id=product['id']) }}">Edit</a>
            <form method="POST" action="{{ url_for('delete_product', product_id=product['id']) }}" style="display:inline;">
                <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                <input type="submit" value="Delete">
            </form>
        </li>
    {% endfor %}
    </ul>
    '''
    return render_template_string(template, products=products)

# Endpoint to add a product
@app.route('/admin/add', methods=['POST'])
@admin_required
def add_product():
    token = request.form.get('csrf_token')
    if not validate_csrf_token(token):
        abort(400, 'Invalid CSRF token')
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    price = request.form.get('price', '').strip()
    if not name or not price:
        return "Name and Price are required", 400
    try:
        price = float(price)
    except ValueError:
        return "Invalid price", 400
    db = get_db()
    db.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
               (name, description, price))
    db.commit()
    return redirect(url_for('admin_panel'))

# Endpoint to edit a product (GET shows form, POST updates data)
@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    db = get_db()
    if request.method == 'POST':
        token = request.form.get('csrf_token')
        if not validate_csrf_token(token):
            abort(400, 'Invalid CSRF token')
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        if not name or not price:
            return "Name and Price are required", 400
        try:
            price = float(price)
        except ValueError:
            return "Invalid price", 400
        db.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?",
                   (name, description, price, product_id))
        db.commit()
        return redirect(url_for('admin_panel'))
    else:
        cur = db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cur.fetchone()
        if product is None:
            return "Product not found", 404
        template = '''
        <h1>Edit Product</h1>
        <form method="POST" action="{{ url_for('edit_product', product_id=product['id']) }}">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            Name: <input type="text" name="name" value="{{ product['name'] }}"><br>
            Description: <textarea name="description">{{ product['description'] }}</textarea><br>
            Price: <input type="number" step="0.01" name="price" value="{{ product['price'] }}"><br>
            <input type="submit" value="Update Product">
        </form>
        <a href="{{ url_for('admin_panel') }}">Back to Admin Panel</a>
        '''
        return render_template_string(template, product=product)

# Endpoint to delete a product
@app.route('/admin/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    token = request.form.get('csrf_token')
    if not validate_csrf_token(token):
        abort(400, 'Invalid CSRF token')
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
