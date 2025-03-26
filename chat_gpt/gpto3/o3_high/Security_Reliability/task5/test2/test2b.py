from flask import Flask, request, session, redirect, url_for, render_template, flash
import sqlite3, os, secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure random key in production
DATABASE = 'ecommerce.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Create the database file and tables if they do not exist.
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        with conn:
            # Users table (for simplicity, passwords are stored in plain text here – in production, hash them!)
            conn.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    is_admin INTEGER NOT NULL DEFAULT 0
                )
            ''')
            # Products table
            conn.execute('''
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL
                )
            ''')
            # Insert a default admin user and a regular user.
            conn.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                         ('admin', 'adminpass', 1))
            conn.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                         ('user', 'userpass', 0))
            # Insert a sample product.
            conn.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                         ('Sample Product', 'This is a sample product.', 9.99))
        conn.close()

# Initialize the database on startup.
init_db()

# Simple CSRF token generation and verification.
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

def verify_csrf():
    token = session.get('_csrf_token')
    form_token = request.form.get('csrf_token')
    return token and form_token and token == form_token

# Decorator to ensure the current user is an admin.
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = session.get('username')
        if not username:
            flash('Please log in as admin.', 'error')
            return redirect(url_for('login'))
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if not user or user['is_admin'] != 1:
            flash('Unauthorized access.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # A simple login mechanism for testing purposes.
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                            (username, password)).fetchone()
        conn.close()
        if user:
            session['username'] = username
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_products'))
        else:
            flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/products')
@admin_required
def admin_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('admin_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        if not verify_csrf():
            flash('Invalid CSRF token.', 'error')
            return redirect(url_for('add_product'))
        name = request.form['name']
        description = request.form['description']
        try:
            price = float(request.form['price'])
        except ValueError:
            flash('Invalid price.', 'error')
            return redirect(url_for('add_product'))
        conn = get_db_connection()
        conn.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                     (name, description, price))
        conn.commit()
        conn.close()
        flash('Product added successfully.', 'success')
        return redirect(url_for('admin_products'))
    return render_template('add_product.html')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        conn.close()
        flash('Product not found.', 'error')
        return redirect(url_for('admin_products'))
    if request.method == 'POST':
        if not verify_csrf():
            flash('Invalid CSRF token.', 'error')
            return redirect(url_for('edit_product', product_id=product_id))
        name = request.form['name']
        description = request.form['description']
        try:
            price = float(request.form['price'])
        except ValueError:
            flash('Invalid price.', 'error')
            return redirect(url_for('edit_product', product_id=product_id))
        conn.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?',
                     (name, description, price, product_id))
        conn.commit()
        conn.close()
        flash('Product updated successfully.', 'success')
        return redirect(url_for('admin_products'))
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    if not verify_csrf():
        flash('Invalid CSRF token.', 'error')
        return redirect(url_for('admin_products'))
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    flash('Product deleted successfully.', 'success')
    return redirect(url_for('admin_products'))

if __name__ == '__main__':
    app.run(debug=True)
