from flask import Flask, request, render_template_string, redirect, url_for, session, g, abort, flash
import sqlite3
import os
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Secret key for session management

DATABASE = 'ecommerce.db'
CSRF_TOKEN_KEY = 'csrf_token'

# --- Database setup ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def create_tables():
    db = get_db()
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("DROP TABLE IF EXISTS products")
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL
        );
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        );
    ''')
    db.commit()

# --- Helper functions ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_csrf_token(token):
    return token == session.get(CSRF_TOKEN_KEY)

# --- Middleware to verify admin ---
def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to be logged in to access this page.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

def admin_required(f):
    @login_required
    def wrap(*args, **kwargs):
        db = get_db()
        user_id = session['user_id']
        user = db.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user or not user[0]:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return wrap

# --- Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        db = get_db()
        user = db.execute('SELECT id, is_admin FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials.", "danger")
    return render_template_string('''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall()
    csrf_token = secrets.token_hex(16)
    session[CSRF_TOKEN_KEY] = csrf_token
    return render_template_string('''
        <h2>Admin Dashboard</h2>
        <p><a href="{{ url_for('logout') }}">Logout</a></p>
        <h3>Products</h3>
        <ul>
            {% for product in products %}
                <li>{{ product[1] }} - ${{ product[3] }}
                <a href="{{ url_for('edit_product', product_id=product[0]) }}">Edit</a>
                <a href="{{ url_for('delete_product', product_id=product[0]) }}" 
                   onclick="return confirm('Are you sure?')">Delete</a></li>
            {% endfor %}
        </ul>
        <h3>Add New Product</h3>
        <form method="post" action="{{ url_for('add_product') }}">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            Name: <input type="text" name="name"><br>
            Description: <input type="text" name="description"><br>
            Price: <input type="number" step="0.01" name="price"><br>
            <input type="submit" value="Add Product">
        </form>
    ''', products=products, csrf_token=csrf_token)

@app.route('/admin/product/add', methods=['POST'])
@admin_required
def add_product():
    if not verify_csrf_token(request.form.get('csrf_token')):
        abort(403)

    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    
    db = get_db()
    db.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
    db.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    db = get_db()
    if request.method == 'POST':
        if not verify_csrf_token(request.form.get('csrf_token')):
            abort(403)

        name = request.form['name']
        description = request.form['description']
        price = request.form['price']

        db.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?', 
                   (name, description, price, product_id))
        db.commit()
        return redirect(url_for('admin_dashboard'))
    
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product:
        csrf_token = secrets.token_hex(16)
        session[CSRF_TOKEN_KEY] = csrf_token
        return render_template_string('''
            <h3>Edit Product</h3>
            <form method="post">
                <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                Name: <input type="text" name="name" value="{{ product[1] }}"><br>
                Description: <input type="text" name="description" value="{{ product[2] }}"><br>
                Price: <input type="number" step="0.01" name="price" value="{{ product[3] }}"><br>
                <input type="submit" value="Save">
            </form>
        ''', product=product, csrf_token=csrf_token)
    else:
        return abort(404)

@app.route('/admin/product/delete/<int:product_id>')
@admin_required
def delete_product(product_id):
    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    # Create tables if they don't exist
    with app.app_context():
        create_tables()
    
    app.run(debug=True)