import os
import sqlite3
import uuid
from functools import wraps
from flask import Flask, request, render_template_string, g, session, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'change-this-secret-key'  # Change this in production!

DATABASE = 'ecommerce.db'

# ------------------------
# Database setup
# ------------------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    # Create tables if they don't exist
    db.executescript('''
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS products;
                     
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            is_admin INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            price REAL
        );
    ''')
    # Insert a test admin user and a regular user if they do not exist
    cur = db.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        db.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ('admin', 1))
        db.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ('user', 0))
    db.commit()

# ------------------------
# CSRF Protection
# ------------------------
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = uuid.uuid4().hex
    return session['_csrf_token']

@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get('_csrf_token', None)
        form_token = request.form.get('_csrf_token')
        if not token or token != form_token:
            return "CSRF validation failed", 400

app.jinja_env.globals['csrf_token'] = generate_csrf_token

# ------------------------
# Admin Check Decorator
# ------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In a real app, you'd check the logged-in user's ID against your user table.
        # Here we assume that session['user_id'] exists and we look up their is_admin flag.
        user_id = session.get('user_id')
        if not user_id:
            flash("You need to log in first.", "error")
            return redirect(url_for('login'))
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or user['is_admin'] != 1:
            return "Access denied: Admins only.", 403
        return f(*args, **kwargs)
    return decorated_function

# ------------------------
# Routes
# ------------------------
# Home page with links for testing
@app.route('/')
def index():
    return render_template_string('''
        <h1>Welcome to the E-commerce Admin Panel</h1>
        <p>
            <a href="{{ url_for('login', user='admin') }}">Login as Admin</a> |
            <a href="{{ url_for('login', user='user') }}">Login as Regular User</a> |
            <a href="{{ url_for('logout') }}">Logout</a>
        </p>
        <p>
            <a href="{{ url_for('admin_dashboard') }}">Admin Dashboard</a>
        </p>
    ''')

# Simple test login route (for demonstration purposes only)
@app.route('/login')
def login():
    user_param = request.args.get('user', 'user')
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (user_param,)).fetchone()
    if user:
        session['user_id'] = user['id']
        flash(f"Logged in as {user['username']}", "info")
    else:
        flash("User not found", "error")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for('index'))

# Admin Dashboard
@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    products = db.execute("SELECT * FROM products").fetchall()
    return render_template_string('''
        <h2>Admin Dashboard</h2>
        <p><a href="{{ url_for('add_product') }}">Add Product</a></p>
        <h3>Products</h3>
        <ul>
        {% for product in products %}
            <li>
                <strong>{{ product.name }}</strong> - ${{ product.price }}<br>
                {{ product.description }}<br>
                <a href="{{ url_for('edit_product', product_id=product.id) }}">Edit</a> |
                <a href="{{ url_for('delete_product', product_id=product.id) }}">Delete</a>
            </li>
        {% endfor %}
        </ul>
        <p><a href="{{ url_for('index') }}">Back to Home</a></p>
    ''', products=products)

# Add Product
@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        try:
            price = float(request.form.get('price'))
        except (ValueError, TypeError):
            flash("Invalid price", "error")
            return redirect(url_for('add_product'))
        db = get_db()
        db.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                   (name, description, price))
        db.commit()
        flash("Product added successfully.", "info")
        return redirect(url_for('admin_dashboard'))
    return render_template_string('''
        <h2>Add Product</h2>
        <form method="POST">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
            <p>Name: <input type="text" name="name" required></p>
            <p>Description: <textarea name="description" required></textarea></p>
            <p>Price: <input type="number" step="0.01" name="price" required></p>
            <p><button type="submit">Add Product</button></p>
        </form>
        <p><a href="{{ url_for('admin_dashboard') }}">Back</a></p>
    ''')

# Edit Product
@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        return "Product not found", 404
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        try:
            price = float(request.form.get('price'))
        except (ValueError, TypeError):
            flash("Invalid price", "error")
            return redirect(url_for('edit_product', product_id=product_id))
        db.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?",
                   (name, description, price, product_id))
        db.commit()
        flash("Product updated.", "info")
        return redirect(url_for('admin_dashboard'))
    return render_template_string('''
        <h2>Edit Product</h2>
        <form method="POST">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
            <p>Name: <input type="text" name="name" value="{{ product.name }}" required></p>
            <p>Description: <textarea name="description" required>{{ product.description }}</textarea></p>
            <p>Price: <input type="number" step="0.01" name="price" value="{{ product.price }}" required></p>
            <p><button type="submit">Update Product</button></p>
        </form>
        <p><a href="{{ url_for('admin_dashboard') }}">Back</a></p>
    ''', product=product)

# Delete Product
@app.route('/admin/delete/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def delete_product(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        return "Product not found", 404
    if request.method == 'POST':
        db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        flash("Product deleted.", "info")
        return redirect(url_for('admin_dashboard'))
    return render_template_string('''
        <h2>Delete Product</h2>
        <p>Are you sure you want to delete <strong>{{ product.name }}</strong>?</p>
        <form method="POST">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
            <button type="submit">Yes, delete it</button>
        </form>
        <p><a href="{{ url_for('admin_dashboard') }}">Cancel</a></p>
    ''', product=product)

# ------------------------
# Initialize and run the app
# ------------------------
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        with app.app_context():
            init_db()
            print("Database initialized.")
    app.run(debug=True)
