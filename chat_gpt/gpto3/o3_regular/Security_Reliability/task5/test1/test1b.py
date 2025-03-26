from flask import Flask, request, render_template_string, redirect, url_for, session, abort, flash
import sqlite3
import os
import uuid
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Used for sessions and CSRF tokens
DATABASE = 'ecommerce.db'

# =======================
# Database initialization
# =======================
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute("DROP TABLE IF EXISTS products")
        
        # Create users table with a simple is_admin flag
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            )
        ''')
        # Create products table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        ''')
        # Insert a test admin user if not exists
        cur = conn.execute("SELECT * FROM users WHERE username = ?", ('admin',))
        if cur.fetchone() is None:
            conn.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ('admin', 1))
    conn.close()

init_db()

# ==========================
# CSRF protection functions
# ==========================
def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = str(uuid.uuid4())
    return session['csrf_token']

def validate_csrf():
    token = session.get('csrf_token', None)
    form_token = request.form.get('csrf_token', '')
    if not token or token != form_token:
        abort(400, description="CSRF validation failed.")

# =====================
# Helper: admin check
# =====================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            abort(403, description="You must be logged in.")
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if not user or not user['is_admin']:
            abort(403, description="Admin privileges required.")
        return f(*args, **kwargs)
    return decorated_function

# ========================
# Simple login simulation
# ========================
@app.route('/login_admin')
def login_admin():
    # For testing, log in as the test admin user
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", ('admin',)).fetchone()
    conn.close()
    if user:
        session['user_id'] = user['id']
        generate_csrf_token()  # Ensure CSRF token is set
        flash("Logged in as admin.", "success")
    return redirect(url_for('list_products'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('list_products'))

# ========================
# Admin: List products
# ========================
@app.route('/admin/products')
@admin_required
def list_products():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    html = '''
    <h1>Products</h1>
    <p><a href="{{ url_for('add_product') }}">Add New Product</a> | <a href="{{ url_for('logout') }}">Logout</a></p>
    <ul>
      {% for p in products %}
        <li>
          <strong>{{ p['name'] }}</strong> - ${{ p['price'] }}<br>
          {{ p['description'] }}<br>
          <a href="{{ url_for('edit_product', product_id=p['id']) }}">Edit</a> | 
          <a href="{{ url_for('delete_product', product_id=p['id']) }}">Delete</a>
        </li>
      {% endfor %}
    </ul>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <ul>
        {% for category, message in messages %}
          <li>{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    '''
    return render_template_string(html, products=products)

# ========================
# Admin: Add product
# ========================
@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        validate_csrf()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        try:
            price = float(request.form.get('price', '0'))
        except ValueError:
            flash("Invalid price.", "error")
            return redirect(url_for('add_product'))

        if not name or price <= 0:
            flash("Name and positive price are required.", "error")
            return redirect(url_for('add_product'))

        conn = get_db_connection()
        conn.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                     (name, description, price))
        conn.commit()
        conn.close()
        flash("Product added.", "success")
        return redirect(url_for('list_products'))
    # GET: render form
    form_html = '''
    <h1>Add Product</h1>
    <form method="post">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <p>Name: <input type="text" name="name" required></p>
      <p>Description: <textarea name="description"></textarea></p>
      <p>Price: <input type="number" step="0.01" name="price" required></p>
      <p><input type="submit" value="Add Product"></p>
    </form>
    <p><a href="{{ url_for('list_products') }}">Back to Products</a></p>
    '''
    return render_template_string(form_html, csrf_token=generate_csrf_token())

# ========================
# Admin: Edit product
# ========================
@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        abort(404, description="Product not found.")

    if request.method == 'POST':
        validate_csrf()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        try:
            price = float(request.form.get('price', '0'))
        except ValueError:
            flash("Invalid price.", "error")
            return redirect(url_for('edit_product', product_id=product_id))

        if not name or price <= 0:
            flash("Name and positive price are required.", "error")
            return redirect(url_for('edit_product', product_id=product_id))

        conn.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?",
                     (name, description, price, product_id))
        conn.commit()
        conn.close()
        flash("Product updated.", "success")
        return redirect(url_for('list_products'))

    conn.close()
    form_html = '''
    <h1>Edit Product</h1>
    <form method="post">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <p>Name: <input type="text" name="name" value="{{ product['name'] }}" required></p>
      <p>Description: <textarea name="description">{{ product['description'] }}</textarea></p>
      <p>Price: <input type="number" step="0.01" name="price" value="{{ product['price'] }}" required></p>
      <p><input type="submit" value="Update Product"></p>
    </form>
    <p><a href="{{ url_for('list_products') }}">Back to Products</a></p>
    '''
    return render_template_string(form_html, product=product, csrf_token=generate_csrf_token())

# ============================
# Admin: Delete product
# ============================
@app.route('/admin/delete/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def delete_product(product_id):
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        abort(404, description="Product not found.")

    if request.method == 'POST':
        validate_csrf()
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()
        flash("Product deleted.", "success")
        return redirect(url_for('list_products'))

    conn.close()
    form_html = '''
    <h1>Delete Product</h1>
    <p>Are you sure you want to delete the product: <strong>{{ product['name'] }}</strong>?</p>
    <form method="post">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <p><input type="submit" value="Confirm Delete"></p>
    </form>
    <p><a href="{{ url_for('list_products') }}">Cancel</a></p>
    '''
    return render_template_string(form_html, product=product, csrf_token=generate_csrf_token())

# ========================
# Default route for testing
# ========================
@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('list_products'))
    else:
        return '<h1>Welcome</h1><p>Please <a href="/login_admin">login as admin</a> for testing.</p>'

if __name__ == '__main__':
    app.run(debug=True)
