from flask import Flask, request, session, redirect, url_for, render_template_string, abort, flash
import sqlite3, os, secrets, functools

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
DATABASE = 'ecommerce.db'

# Helper function to get a database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database (create tables and insert sample data) if it doesn't exist
def init_db():
    if not os.path.exists(DATABASE):
        conn = get_db()
        cur = conn.cursor()
        # Create a simple users table
        cur.execute("DROP TABLE IF EXISTS users")
        cur.execute("DROP TABLE IF EXISTS products")
        cur.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                is_admin INTEGER NOT NULL
            )
        ''')
        # Create a products table
        cur.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        ''')
        # Insert sample users: one admin and one regular user
        cur.execute('INSERT INTO users (username, is_admin) VALUES (?, ?)', ('admin', 1))
        cur.execute('INSERT INTO users (username, is_admin) VALUES (?, ?)', ('user', 0))
        # Insert a sample product
        cur.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                    ('Sample Product', 'This is a sample product.', 9.99))
        conn.commit()
        conn.close()

init_db()

# CSRF token generation and injection into templates
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf_token())

# Verify that the CSRF token in the form matches the one in session
def verify_csrf_token():
    token = session.get('_csrf_token', None)
    form_token = request.form.get('_csrf_token')
    if not token or token != form_token:
        abort(400, description="Invalid CSRF token")

# Decorator to require that a user is logged in
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Decorator to ensure that the logged-in user is an admin
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT is_admin FROM users WHERE id = ?", (session['user_id'],))
        user = cur.fetchone()
        conn.close()
        if not user or user['is_admin'] != 1:
            abort(403, description="Access denied: Admins only.")
        return f(*args, **kwargs)
    return decorated_function

# A simple login route for testing (no passwords; just choose a username)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            flash('Logged in as {}'.format(username))
            return redirect(url_for('admin_products'))
        else:
            flash('User not found')
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
            <label>Username:</label>
            <input type="text" name="username">
            <input type="submit" value="Login">
        </form>
        <p>Test with username "admin" (for admin privileges) or "user" (non-admin).</p>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Display the list of products with admin controls
@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    conn.close()
    return render_template_string('''
        <h2>Product List</h2>
        <a href="{{ url_for('add_product') }}">Add New Product</a>
        <ul>
        {% for product in products %}
            <li>
                <strong>{{ product['name'] }}</strong> - ${{ product['price'] }}<br>
                {{ product['description'] }}<br>
                <a href="{{ url_for('edit_product', product_id=product['id']) }}">Edit</a> |
                <form action="{{ url_for('delete_product', product_id=product['id']) }}" method="post" style="display:inline;">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                    <input type="submit" value="Delete" onclick="return confirm('Are you sure?');">
                </form>
            </li>
        {% endfor %}
        </ul>
        <a href="{{ url_for('logout') }}">Logout</a>
    ''', products=products)

# Route to add a new product
@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        verify_csrf_token()
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        if not name or not price:
            flash("Name and Price are required.")
            return redirect(url_for('add_product'))
        try:
            price = float(price)
        except ValueError:
            flash("Invalid price.")
            return redirect(url_for('add_product'))
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                    (name, description, price))
        conn.commit()
        conn.close()
        flash("Product added successfully.")
        return redirect(url_for('admin_products'))
    return render_template_string('''
        <h2>Add New Product</h2>
        <form method="post">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
            <label>Name:</label>
            <input type="text" name="name"><br>
            <label>Description:</label>
            <textarea name="description"></textarea><br>
            <label>Price:</label>
            <input type="text" name="price"><br>
            <input type="submit" value="Add Product">
        </form>
        <a href="{{ url_for('admin_products') }}">Back to Product List</a>
    ''')

# Route to edit an existing product
@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'POST':
        verify_csrf_token()
        # Verify that the product exists before modifying
        cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cur.fetchone()
        if not product:
            conn.close()
            abort(404, description="Product not found")
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        if not name or not price:
            flash("Name and Price are required.")
            conn.close()
            return redirect(url_for('edit_product', product_id=product_id))
        try:
            price = float(price)
        except ValueError:
            flash("Invalid price.")
            conn.close()
            return redirect(url_for('edit_product', product_id=product_id))
        cur.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?",
                    (name, description, price, product_id))
        conn.commit()
        conn.close()
        flash("Product updated successfully.")
        return redirect(url_for('admin_products'))
    else:
        # GET request: Verify product exists before showing the form
        cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cur.fetchone()
        conn.close()
        if not product:
            abort(404, description="Product not found")
        return render_template_string('''
            <h2>Edit Product</h2>
            <form method="post">
                <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                <label>Name:</label>
                <input type="text" name="name" value="{{ product['name'] }}"><br>
                <label>Description:</label>
                <textarea name="description">{{ product['description'] }}</textarea><br>
                <label>Price:</label>
                <input type="text" name="price" value="{{ product['price'] }}"><br>
                <input type="submit" value="Update Product">
            </form>
            <a href="{{ url_for('admin_products') }}">Back to Product List</a>
        ''', product=product)

# Route to delete a product (via POST to enforce CSRF protection)
@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    verify_csrf_token()
    conn = get_db()
    cur = conn.cursor()
    # Verify that the product exists before deletion
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()
    if not product:
        conn.close()
        abort(404, description="Product not found")
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    flash("Product deleted successfully.")
    return redirect(url_for('admin_products'))


if __name__ == '__main__':
    app.run(debug=True)
