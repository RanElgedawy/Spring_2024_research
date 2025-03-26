from flask import Flask, request, render_template_string, redirect, url_for, session, flash
import sqlite3
import hashlib
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Secret key for session management and CSRF protection

# CSRF protection function
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

def verify_csrf_token(token):
    return token == session.pop('_csrf_token', None)

app.jinja_env.globals['csrf_token'] = generate_csrf_token

# Initialize the database
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")

    # Create a users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT,
                    is_admin INTEGER)''')
    
    c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (1, 'test', 'test', 0))

    # Create a products table
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    price REAL)''')

    # Add a sample admin user (username: admin, password: admin123)
    hashed_password = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)", 
              ('admin', hashed_password, 1))

    conn.commit()
    conn.close()

# Authenticate user (simple for this example)
def authenticate(username, password):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = c.fetchone()
    conn.close()
    if user:
        return user
    return None

# Verify if the user is an admin
def is_admin():
    return session.get('is_admin', False)

# Sanitize input (for basic XSS protection)
def sanitize_input(input_string):
    return input_string.replace("<", "&lt;").replace(">", "&gt;")

# Routes

@app.route('/')
def index():
    return "Welcome to the e-commerce site!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate(username, password)
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[3] == 1
            flash("Logged in successfully!", "success")
            return redirect(url_for('admin_panel'))
        else:
            flash("Invalid credentials", "danger")
    
    return render_template_string('''
        <form method="POST">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if not is_admin():
        return "Access denied", 403

    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    # Fetch all products for display
    c.execute("SELECT * FROM products")
    products = c.fetchall()

    if request.method == 'POST':
        if not verify_csrf_token(request.form.get('_csrf_token')):
            flash("Invalid CSRF token", "danger")
            return redirect(url_for('admin_panel'))

        action = request.form['action']
        product_name = sanitize_input(request.form['name'])
        product_description = sanitize_input(request.form['description'])
        product_price = float(request.form['price'])

        if action == 'add':
            c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", 
                      (product_name, product_description, product_price))
        elif action == 'edit':
            product_id = int(request.form['product_id'])
            c.execute("UPDATE products SET name=?, description=?, price=? WHERE id=?", 
                      (product_name, product_description, product_price, product_id))
        elif action == 'delete':
            product_id = int(request.form['product_id'])
            c.execute("DELETE FROM products WHERE id=?", (product_id,))

        conn.commit()
        flash(f"Product {action}ed successfully!", "success")

    conn.close()
    
    return render_template_string('''
        <h1>Admin Panel</h1>
        <h2>Products</h2>
        <ul>
        {% for product in products %}
            <li>{{ product[1] }} - {{ product[2] }} - ${{ product[3] }}
                <form method="POST" style="display:inline;">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
                    <input type="hidden" name="product_id" value="{{ product[0] }}">
                    <input type="submit" name="action" value="delete">
                </form>
            </li>
        {% endfor %}
        </ul>
        <h3>Add/Edit Product</h3>
        <form method="POST">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
            Name: <input type="text" name="name"><br>
            Description: <input type="text" name="description"><br>
            Price: <input type="text" name="price"><br>
            Product ID (for edit/delete): <input type="text" name="product_id"><br>
            <input type="submit" name="action" value="add">
            <input type="submit" name="action" value="edit">
        </form>
    ''', products=products)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)