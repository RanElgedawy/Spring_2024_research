from flask import Flask, request, session, redirect, url_for, render_template_string, flash, g
import sqlite3, os, secrets

DATABASE = 'app.db'
SECRET_KEY = secrets.token_hex(16)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# ----------------------
# Database Helpers
# ----------------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    # Create users table (if not exists)
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("DROP TABLE IF EXISTS products")

    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT, -- in production, store a hash!
            admin BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    # Create products table (if not exists)
    db.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    db.commit()
    # For testing, insert a default admin user if not present
    cur = db.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if cur.fetchone() is None:
        db.execute("INSERT INTO users (username, password, admin) VALUES (?, ?, ?)",
                   ("admin", "adminpass", True))
        db.commit()
    
    # For testing, insert a default non-admin user if not present
    cur = db.execute("SELECT * FROM users WHERE username = ?", ("user",))
    if cur.fetchone() is None:
        db.execute("INSERT INTO users (username, password, admin) VALUES (?, ?, ?)",
                ("user", "userpass", False))
        db.commit()

# ----------------------
# CSRF Token Helpers
# ----------------------
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

def validate_csrf(token):
    return token and token == session.get('_csrf_token')

app.jinja_env.globals['csrf_token'] = generate_csrf_token

# ----------------------
# Simple Login Simulation
# ----------------------
# In this demo, go to /login?username=admin to simulate an admin login.
@app.route('/login')
def login():
    username = request.args.get('username')
    if not username:
        return "Please provide a username in the query string (e.g. ?username=admin)", 400
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user:
        session['user'] = {'id': user['id'], 'username': user['username'], 'admin': bool(user['admin'])}
        return redirect(url_for('admin_products'))
    else:
        return "User not found", 404

# A simple logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return "Logged out"

def admin_required():
    user = session.get('user')
    if not user or not user.get('admin'):
        return False
    return True

# ----------------------
# Admin Product Management
# ----------------------
@app.route('/admin/products', methods=['GET', 'POST'])
def admin_products():
    if not admin_required():
        return "Access denied: Admins only", 403

    db = get_db()
    message = ""
    
    # Handle POST requests for add/update/delete operations
    if request.method == 'POST':
        # Check CSRF token
        token = request.form.get('csrf_token')
        if not validate_csrf(token):
            return "Invalid CSRF token", 400

        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            try:
                price = float(request.form.get('price', '0'))
            except ValueError:
                price = 0
            if name and price > 0:
                db.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                           (name, description, price))
                db.commit()
                message = "Product added."
            else:
                message = "Invalid input for product addition."
        elif action == 'update':
            try:
                prod_id = int(request.form.get('id'))
            except (TypeError, ValueError):
                prod_id = None
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            try:
                price = float(request.form.get('price', '0'))
            except ValueError:
                price = 0
            if prod_id and name and price > 0:
                db.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?",
                           (name, description, price, prod_id))
                db.commit()
                message = "Product updated."
            else:
                message = "Invalid input for product update."
        elif action == 'delete':
            try:
                prod_id = int(request.form.get('id'))
            except (TypeError, ValueError):
                prod_id = None
            if prod_id:
                db.execute("DELETE FROM products WHERE id = ?", (prod_id,))
                db.commit()
                message = "Product deleted."
            else:
                message = "Invalid product id for deletion."
        else:
            message = "Unknown action."

    # Retrieve current products for display
    products = db.execute("SELECT * FROM products").fetchall()

    # Basic HTML template with forms and autoescaped output
    template = '''
    <!doctype html>
    <html>
      <head>
        <title>Admin Product Management</title>
      </head>
      <body>
        <h1>Admin Product Management</h1>
        <p style="color:green;">{{ message }}</p>
        <h2>Add New Product</h2>
        <form method="POST">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <input type="hidden" name="action" value="add">
          <label>Name: <input type="text" name="name"></label><br>
          <label>Description: <textarea name="description"></textarea></label><br>
          <label>Price: <input type="text" name="price"></label><br>
          <button type="submit">Add Product</button>
        </form>
        <hr>
        <h2>Existing Products</h2>
        {% for prod in products %}
          <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
            <strong>ID:</strong> {{ prod.id }}<br>
            <strong>Name:</strong> {{ prod.name }}<br>
            <strong>Description:</strong> {{ prod.description }}<br>
            <strong>Price:</strong> {{ prod.price }}<br>
            <form method="POST" style="display:inline-block;">
              <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
              <input type="hidden" name="action" value="delete">
              <input type="hidden" name="id" value="{{ prod.id }}">
              <button type="submit" onclick="return confirm('Are you sure you want to delete this product?');">Delete</button>
            </form>
            <button onclick="document.getElementById('update-{{ prod.id }}').style.display='block';">Update</button>
            <div id="update-{{ prod.id }}" style="display:none;">
              <form method="POST">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <input type="hidden" name="action" value="update">
                <input type="hidden" name="id" value="{{ prod.id }}">
                <label>Name: <input type="text" name="name" value="{{ prod.name }}"></label><br>
                <label>Description: <textarea name="description">{{ prod.description }}</textarea></label><br>
                <label>Price: <input type="text" name="price" value="{{ prod.price }}"></label><br>
                <button type="submit">Update Product</button>
              </form>
            </div>
          </div>
        {% else %}
          <p>No products available.</p>
        {% endfor %}
      </body>
    </html>
    '''
    return render_template_string(template, products=products, message=message)

# ----------------------
# Index and Setup
# ----------------------
@app.route('/')
def index():
    return '''
    <h1>Welcome to the E-commerce Admin Panel Demo</h1>
    <p>To test, log in as admin: <a href="/login?username=admin">/login?username=admin</a></p>
    <p>Then go to <a href="/admin/products">Admin Product Management</a></p>
    '''

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        with app.app_context():
            init_db()
    app.run(debug=True)
