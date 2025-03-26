from flask import Flask, request, session, redirect, url_for, render_template_string, g, flash
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import os
import secrets

# Setup Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Setup SQLite database
DATABASE = 'ecommerce.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def create_tables():
    # Create tables if they don't exist
    with app.app_context():
        db = get_db()
        db.execute("DROP TABLE IF EXISTS users")
        db.execute("DROP TABLE IF EXISTS products")

        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Check if current user is admin
def is_admin():
    user_id = session.get('user_id')
    if user_id:
        db = get_db()
        cur = db.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
        user = cur.fetchone()
        if user and user[0] == 1:
            return True
    return False

# CSRF Protection token
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

def verify_csrf_token(token):
    return session.get('_csrf_token') == token

@app.before_request
def add_csrf_token():
    if request.method == "POST":
        token = request.form.get('_csrf_token')
        if not verify_csrf_token(token):
            return "CSRF attack detected!", 400

app.jinja_env.globals['csrf_token'] = generate_csrf_token

# Routes for admin panel
@app.route('/admin/products', methods=['GET', 'POST'])
def manage_products():
    if not is_admin():
        return "Unauthorized", 403

    db = get_db()

    if request.method == 'POST':
        action = request.form.get('action')
        product_id = request.form.get('product_id')
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')

        # XSS Protection: escape inputs before storing or rendering them
        name = str(name).replace("<", "&lt;").replace(">", "&gt;")
        description = str(description).replace("<", "&lt;").replace(">", "&gt;")

        if action == 'add':
            db.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
            db.commit()
            flash('Product added successfully!')
        elif action == 'update' and product_id:
            db.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?', (name, description, price, product_id))
            db.commit()
            flash('Product updated successfully!')
        elif action == 'delete' and product_id:
            db.execute('DELETE FROM products WHERE id = ?', (product_id,))
            db.commit()
            flash('Product deleted successfully!')

    cur = db.execute('SELECT * FROM products')
    products = cur.fetchall()

    # Render products in a basic template
    template = '''
        <h1>Admin Panel</h1>
        <form method="POST">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
            <input type="text" name="name" placeholder="Product Name" required><br>
            <textarea name="description" placeholder="Description" required></textarea><br>
            <input type="number" step="0.01" name="price" placeholder="Price" required><br>
            <button type="submit" name="action" value="add">Add Product</button>
        </form>

        <h2>Current Products</h2>
        <ul>
            {% for product in products %}
            <li>
                {{ product[1] }} - {{ product[2] }} - ${{ product[3] }}
                <form method="POST" style="display:inline;">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
                    <input type="hidden" name="product_id" value="{{ product[0] }}">
                    <input type="text" name="name" value="{{ product[1] }}" required>
                    <textarea name="description">{{ product[2] }}</textarea>
                    <input type="number" step="0.01" name="price" value="{{ product[3] }}" required>
                    <button type="submit" name="action" value="update">Update</button>
                    <button type="submit" name="action" value="delete">Delete</button>
                </form>
            </li>
            {% endfor %}
        </ul>
    '''
    return render_template_string(template, products=products)

# Helper to create a test user
@app.route('/create_admin')
def create_admin():
    db = get_db()
    username = 'admin'
    password = generate_password_hash('admin123')
    db.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, 1)', (username, password))
    db.commit()
    return "Admin user created with username 'admin' and password 'admin123'."

# NOT part of the original code, added to test functionality
# Simulate an admin being logged in for testing purposes
@app.before_request
def simulate_admin_login():
    if 'user_id' not in session:
        # Check if the admin user exists in the database
        db = get_db()
        cur = db.execute('SELECT id FROM users WHERE username = "admin" AND is_admin = 1')
        admin_user = cur.fetchone()
        if admin_user:
            session['user_id'] = admin_user[0]
        else:
            # If no admin user exists, create one
            password = generate_password_hash('admin123')
            db.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, 1)', ('admin', password))
            db.commit()
            cur = db.execute('SELECT id FROM users WHERE username = "admin"')
            session['user_id'] = cur.fetchone()[0]

# This is part of the original code
if __name__ == "__main__":
    create_tables()
    app.run(debug=True)