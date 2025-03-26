from flask import Flask, request, session, redirect, url_for, render_template_string, abort
import sqlite3, os, secrets

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key in production
DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Create users table
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS products")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            is_admin INTEGER NOT NULL
        )
    ''')
    # Create products table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    # Insert a default admin user if not exists
    cur.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if cur.fetchone() is None:
        cur.execute('INSERT INTO users (username, is_admin) VALUES (?, ?)', ('admin', 1))
    # Insert a default non-admin user if not exists
    cur.execute('SELECT * FROM users WHERE username = ?', ('user',))
    if cur.fetchone() is None:
        cur.execute('INSERT INTO users (username, is_admin) VALUES (?, ?)', ('user', 0))
    conn.commit()
    conn.close()

@app.before_first_request
def setup():
    init_db()

# CSRF token generation and injection into templates
def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf_token())

# Helper: Ensure the current user is an admin.
def admin_required():
    if not session.get('is_admin'):
        abort(403)

# Dummy login/logout routes for testing purposes.
@app.route('/login', methods=['GET'])
def login():
    username = request.args.get('username')
    if not username:
        return 'Please provide a username in the query string, e.g., /login?username=admin'
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    if user:
        session['username'] = user['username']
        session['is_admin'] = bool(user['is_admin'])
        return redirect(url_for('admin_dashboard'))
    else:
        return 'User not found.'

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template_string('''
        <h1>Admin Dashboard</h1>
        <p>Logged in as: {{ session.username }} {% if session.is_admin %}(Admin){% else %}(Non-admin){% endif %}</p>
        <p><a href="{{ url_for('list_products') }}">Manage Products</a></p>
        <p><a href="{{ url_for('logout') }}">Logout</a></p>
    ''')

# List products with options to edit or delete.
@app.route('/admin/products')
def list_products():
    admin_required()
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template_string('''
        <h1>Product List</h1>
        <a href="{{ url_for('add_product') }}">Add New Product</a>
        <ul>
        {% for product in products %}
            <li>
                <strong>{{ product.name|e }}</strong> - ${{ product.price }}<br>
                {{ product.description|e }}<br>
                <a href="{{ url_for('edit_product', product_id=product.id) }}">Edit</a>
                <form action="{{ url_for('delete_product', product_id=product.id) }}" method="post" style="display:inline;">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                    <button type="submit" onclick="return confirm('Are you sure?');">Delete</button>
                </form>
            </li>
        {% else %}
            <li>No products available.</li>
        {% endfor %}
        </ul>
        <p><a href="{{ url_for('admin_dashboard') }}">Back to Dashboard</a></p>
    ''', products=products)

# Add a new product.
@app.route('/admin/products/add', methods=['GET', 'POST'])
def add_product():
    admin_required()
    if request.method == 'POST':
        # Verify CSRF token
        if request.form.get('csrf_token') != session.get('csrf_token'):
            abort(400, description="CSRF token missing or incorrect.")
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        if not name or not price:
            return 'Name and price are required.', 400
        try:
            price = float(price)
        except ValueError:
            return 'Invalid price.', 400
        conn = get_db_connection()
        conn.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                     (name, description, price))
        conn.commit()
        conn.close()
        return redirect(url_for('list_products'))
    return render_template_string('''
        <h1>Add Product</h1>
        <form method="post">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label>Name: <input type="text" name="name"></label><br>
            <label>Description: <textarea name="description"></textarea></label><br>
            <label>Price: <input type="text" name="price"></label><br>
            <button type="submit">Add Product</button>
        </form>
        <p><a href="{{ url_for('list_products') }}">Back to Product List</a></p>
    ''')

# Edit an existing product.
@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    admin_required()
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        conn.close()
        return 'Product not found.', 404
    if request.method == 'POST':
        if request.form.get('csrf_token') != session.get('csrf_token'):
            conn.close()
            abort(400, description="CSRF token missing or incorrect.")
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        if not name or not price:
            conn.close()
            return 'Name and price are required.', 400
        try:
            price = float(price)
        except ValueError:
            conn.close()
            return 'Invalid price.', 400
        conn.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?',
                     (name, description, price, product_id))
        conn.commit()
        conn.close()
        return redirect(url_for('list_products'))
    conn.close()
    return render_template_string('''
        <h1>Edit Product</h1>
        <form method="post">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label>Name: <input type="text" name="name" value="{{ product.name|e }}"></label><br>
            <label>Description: <textarea name="description">{{ product.description|e }}</textarea></label><br>
            <label>Price: <input type="text" name="price" value="{{ product.price }}"></label><br>
            <button type="submit">Update Product</button>
        </form>
        <p><a href="{{ url_for('list_products') }}">Back to Product List</a></p>
    ''', product=product)

# Delete a product.
@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    admin_required()
    if request.form.get('csrf_token') != session.get('csrf_token'):
        abort(400, description="CSRF token missing or incorrect.")
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('list_products'))

if __name__ == '__main__':
    app.run(debug=True)
