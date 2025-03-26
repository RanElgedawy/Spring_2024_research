from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3
import hashlib
import os
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management and CSRF protection

DATABASE = 'products.db'

# Database connection setup
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Create necessary tables if they don't exist
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Users table (with admin role)
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL CHECK (is_admin IN (0, 1))
        )''')

        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (1, 'test', 'test', 1))

        # Products table
        cursor.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL
        )''')
        db.commit()

# Check if the logged-in user is admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        if user is None or user[0] != 1:
            flash("You do not have admin privileges.")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# CSRF token generator and validator
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = hashlib.sha256(os.urandom(64)).hexdigest()
    return session['_csrf_token']

@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            flash("CSRF token is invalid.")
            return redirect(url_for('index'))

app.jinja_env.globals['csrf_token'] = generate_csrf_token

# Prevent XSS: sanitize input
def sanitize_input(input_text):
    return re.sub(r'[<>]', '', input_text)

@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return render_template('index.html', products=products)

# Admin: Add Product
@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = sanitize_input(request.form['name'])
        description = sanitize_input(request.form['description'])
        price = float(request.form['price'])
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
        db.commit()
        flash('Product added successfully.')
        return redirect(url_for('index'))
    return render_template('add_product.html')

# Admin: Modify Product
@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    
    if request.method == 'POST':
        name = sanitize_input(request.form['name'])
        description = sanitize_input(request.form['description'])
        price = float(request.form['price'])
        
        cursor.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?", (name, description, price, product_id))
        db.commit()
        flash('Product updated successfully.')
        return redirect(url_for('index'))
    
    return render_template('edit_product.html', product=product)

# Admin: Remove Product
@app.route('/admin/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    flash('Product deleted successfully.')
    return redirect(url_for('index'))

# Admin/User login (basic authentication for testing)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = sanitize_input(request.form['username'])
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user[0]
            flash("Logged in successfully.")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()  # Initialize the database with necessary tables
    app.run(debug=True)