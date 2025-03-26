from flask import Flask, request, render_template_string, redirect, url_for, session, abort, flash
import sqlite3
import os
import functools

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for sessions and CSRF protection

DATABASE = 'ecommerce.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Create a simple users table (with an admin flag)
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS products")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            is_admin INTEGER NOT NULL DEFAULT 0
        );
    ''')
    # Create a products table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        );
    ''')
    conn.commit()
    # Create a default admin user if one does not exist
    cur.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ("admin", 1))
        conn.commit()
    conn.close()

@app.before_first_request
def initialize():
    init_db()
    # Ensure a CSRF token exists in the session for forms
    if 'csrf_token' not in session:
        session['csrf_token'] = os.urandom(16).hex()

def admin_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            abort(403)
        return func(*args, **kwargs)
    return wrapper

# --- Simulated login routes for testing ---

@app.route('/login/admin')
def login_admin():
    # For demonstration, we simply set session variables.
    # In production, use a proper authentication mechanism.
    session['user_id'] = 1  # Assuming the default admin has id 1
    session['is_admin'] = True
    flash("Logged in as admin.", "success")
    return redirect(url_for('admin_products'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for('admin_products'))

# --- Admin routes for managing products ---

@app.route('/admin/products')
@admin_required
def admin_products():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    # Autoescaping in Jinja2 helps protect against XSS
    return render_template_string('''
        <h1>Admin: Manage Products</h1>
        <p><a href="{{ url_for('add_product') }}">Add New Product</a></p>
        <ul>
          {% for product in products %}
          <li>
             <strong>{{ product['name'] }}</strong> - ${{ product['price'] }}<br>
             {{ product['description'] }}<br>
             <a href="{{ url_for('edit_product', product_id=product['id']) }}">Edit</a>
             <form action="{{ url_for('delete_product', product_id=product['id']) }}" method="post" style="display:inline;">
                <input type="hidden" name="csrf_token" value="{{ session['csrf_token'] }}">
                <button type="submit" onclick="return confirm('Are you sure?')">Delete</button>
             </form>
          </li>
          {% endfor %}
        </ul>
        <p><a href="{{ url_for('logout') }}">Logout</a></p>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <ul>
              {% for category, message in messages %}
                <li>{{ message }}</li>
              {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
    ''', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        # Verify CSRF token
        if request.form.get('csrf_token') != session.get('csrf_token'):
            abort(400, "Invalid CSRF token")
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        if not name or not price:
            flash("Name and price are required.", "error")
        else:
            try:
                price = float(price)
            except ValueError:
                flash("Invalid price.", "error")
                return redirect(url_for('add_product'))
            conn = get_db_connection()
            conn.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                         (name, description, price))
            conn.commit()
            conn.close()
            flash("Product added successfully.", "success")
            return redirect(url_for('admin_products'))
    return render_template_string('''
        <h1>Add Product</h1>
        <form method="post">
           <input type="hidden" name="csrf_token" value="{{ session['csrf_token'] }}">
           <p>Name: <input type="text" name="name"></p>
           <p>Description: <textarea name="description"></textarea></p>
           <p>Price: <input type="text" name="price"></p>
           <p><button type="submit">Add Product</button></p>
        </form>
        <p><a href="{{ url_for('admin_products') }}">Back to Products</a></p>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <ul>
              {% for category, message in messages %}
                <li>{{ message }}</li>
              {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
    ''')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        conn.close()
        abort(404)
    if request.method == 'POST':
        # Verify CSRF token
        if request.form.get('csrf_token') != session.get('csrf_token'):
            abort(400, "Invalid CSRF token")
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        if not name or not price:
            flash("Name and price are required.", "error")
        else:
            try:
                price = float(price)
            except ValueError:
                flash("Invalid price.", "error")
                return redirect(url_for('edit_product', product_id=product_id))
            conn.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?",
                         (name, description, price, product_id))
            conn.commit()
            conn.close()
            flash("Product updated successfully.", "success")
            return redirect(url_for('admin_products'))
    conn.close()
    return render_template_string('''
        <h1>Edit Product</h1>
        <form method="post">
           <input type="hidden" name="csrf_token" value="{{ session['csrf_token'] }}">
           <p>Name: <input type="text" name="name" value="{{ product['name'] }}"></p>
           <p>Description: <textarea name="description">{{ product['description'] }}</textarea></p>
           <p>Price: <input type="text" name="price" value="{{ product['price'] }}"></p>
           <p><button type="submit">Update Product</button></p>
        </form>
        <p><a href="{{ url_for('admin_products') }}">Back to Products</a></p>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <ul>
              {% for category, message in messages %}
                <li>{{ message }}</li>
              {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
    ''', product=product)

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    # Verify CSRF token
    if request.form.get('csrf_token') != session.get('csrf_token'):
        abort(400, "Invalid CSRF token")
    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    flash("Product deleted successfully.", "success")
    return redirect(url_for('admin_products'))

if __name__ == '__main__':
    # Run in debug mode for testing. In production, disable debug.
    app.run(debug=True)
