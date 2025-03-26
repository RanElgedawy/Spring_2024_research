from flask import Flask, request, session, redirect, url_for, render_template_string, abort, flash
import sqlite3, os, secrets
from functools import wraps

app = Flask(__name__)
# Use a secure random secret key for session management
app.secret_key = os.urandom(24)
DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they do not exist."""
    db = get_db()
    cursor = db.cursor()
    # Create products table
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    )''')
    # Create a simple users table to demo admin privileges
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0
    )''')
    # Insert a sample admin user for testing
    cursor.execute("INSERT OR IGNORE INTO users (username, is_admin) VALUES (?, ?)", ('admin', 1))
    db.commit()
    db.close()

init_db()

# --- CSRF Protection ---
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

def csrf_protect(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('_csrf_token')
        form_token = request.form.get('_csrf_token')
        if not token or token != form_token:
            abort(400, description="CSRF token missing or incorrect")
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Check ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For simplicity, we assume a logged-in user is stored in session as "username"
        if 'username' not in session:
            abort(403, description="Access denied: You must be logged in as an admin.")
        # Verify admin privileges from the database
        db = get_db()
        cur = db.execute("SELECT is_admin FROM users WHERE username = ?", (session['username'],))
        user = cur.fetchone()
        db.close()
        if not user or user['is_admin'] != 1:
            abort(403, description="Access denied: Admin privileges required.")
        return f(*args, **kwargs)
    return decorated_function

# --- Routes for Testing Login ---
# These routes let you simulate logging in/out. In production the login mechanism would be more robust.
@app.route('/login/<username>')
def login(username):
    session['username'] = username
    flash(f"Logged in as {username}")
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out")
    return redirect(url_for('admin_panel'))

# --- Admin Panel ---
@app.route('/admin', methods=['GET'])
@admin_required
def admin_panel():
    db = get_db()
    cur = db.execute("SELECT * FROM products")
    products = cur.fetchall()
    db.close()
    html = '''
    <h1>Admin Panel</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
          {% for message in messages %}
            <li>{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <p><a href="{{ url_for('logout') }}">Logout</a></p>
    <h2>Add Product</h2>
    <form method="post" action="{{ url_for('add_product') }}">
      <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
      <p>Name: <input type="text" name="name" required></p>
      <p>Description: <textarea name="description"></textarea></p>
      <p>Price: <input type="number" step="0.01" name="price" required></p>
      <p><input type="submit" value="Add Product"></p>
    </form>
    
    <h2>Existing Products</h2>
    <ul>
      {% for product in products %}
        <li>
          <strong>{{ product['name'] }}</strong> - ${{ product['price'] }}<br>
          {{ product['description'] | e }}<br>
          <a href="{{ url_for('edit_product', product_id=product['id']) }}">Edit</a> |
          <a href="{{ url_for('confirm_delete', product_id=product['id']) }}">Delete</a>
        </li>
      {% endfor %}
    </ul>
    '''
    return render_template_string(html, products=products)

# --- Add Product ---
@app.route('/admin/add', methods=['POST'])
@admin_required
@csrf_protect
def add_product():
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    if not name or not price:
        flash("Name and price are required.")
        return redirect(url_for('admin_panel'))
    try:
        price = float(price)
    except ValueError:
        flash("Invalid price format.")
        return redirect(url_for('admin_panel'))
    db = get_db()
    db.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
    db.commit()
    db.close()
    flash("Product added successfully.")
    return redirect(url_for('admin_panel'))

# --- Edit Product ---
@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    db = get_db()
    if request.method == 'POST':
        # CSRF protection
        token = session.get('_csrf_token')
        form_token = request.form.get('_csrf_token')
        if not token or token != form_token:
            abort(400, description="CSRF token missing or incorrect")
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        if not name or not price:
            flash("Name and price are required.")
            return redirect(url_for('edit_product', product_id=product_id))
        try:
            price = float(price)
        except ValueError:
            flash("Invalid price format.")
            return redirect(url_for('edit_product', product_id=product_id))
        db.execute("UPDATE products SET name=?, description=?, price=? WHERE id=?", (name, description, price, product_id))
        db.commit()
        db.close()
        flash("Product updated successfully.")
        return redirect(url_for('admin_panel'))
    else:
        cur = db.execute("SELECT * FROM products WHERE id=?", (product_id,))
        product = cur.fetchone()
        db.close()
        if not product:
            abort(404, description="Product not found.")
        html = '''
        <h1>Edit Product</h1>
        <form method="post" action="{{ url_for('edit_product', product_id=product['id']) }}">
          <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
          <p>Name: <input type="text" name="name" value="{{ product['name'] }}" required></p>
          <p>Description: <textarea name="description">{{ product['description'] }}</textarea></p>
          <p>Price: <input type="number" step="0.01" name="price" value="{{ product['price'] }}" required></p>
          <p><input type="submit" value="Update Product"></p>
        </form>
        <p><a href="{{ url_for('admin_panel') }}">Back to Admin Panel</a></p>
        '''
        return render_template_string(html, product=product)

# --- Confirm Delete Product ---
@app.route('/admin/confirm_delete/<int:product_id>', methods=['GET'])
@admin_required
def confirm_delete(product_id):
    db = get_db()
    cur = db.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cur.fetchone()
    db.close()
    if not product:
        abort(404, description="Product not found.")
    html = '''
    <h1>Confirm Delete</h1>
    <p>Are you sure you want to delete "{{ product['name'] }}"?</p>
    <form method="post" action="{{ url_for('delete_product', product_id=product['id']) }}">
      <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
      <input type="submit" value="Confirm Delete">
    </form>
    <p><a href="{{ url_for('admin_panel') }}">Cancel</a></p>
    '''
    return render_template_string(html, product=product)

# --- Delete Product ---
@app.route('/admin/delete/<int:product_id>', methods=['POST'])
@admin_required
@csrf_protect
def delete_product(product_id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id=?", (product_id,))
    db.commit()
    db.close()
    flash("Product deleted successfully.")
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)
