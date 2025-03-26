from flask import Flask, request, jsonify, g, abort
import sqlite3

DATABASE = 'ecommerce.db'
app = Flask(__name__)

# -----------------------------
# Database helpers
# -----------------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        # Return rows as dictionaries for convenience.
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database with user and product tables, and sample data."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")

    # Create user table with an is_admin flag (1 means admin)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    ''')
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    db.commit()

    # Insert sample users if they do not exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        users = [
            ('admin_user', 1),    # admin
            ('regular_user', 0)   # non-admin
        ]
        cursor.executemany("INSERT INTO users (username, is_admin) VALUES (?,?)", users)
        db.commit()

    # Insert a sample product if none exists
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                       ('Sample Product', 'A sample product for testing.', 9.99))
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# -----------------------------
# Helper: Verify admin privileges
# -----------------------------
def get_current_user():
    """
    Simulate logged in user by reading the 'X-User-ID' header.
    Returns a user dictionary or aborts if user not found.
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        abort(400, description="Missing X-User-ID header")
    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    if not user:
        abort(400, description="User not found")
    return user

def admin_required(func):
    """
    Decorator to ensure the current user is an admin.
    """
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user['is_admin'] != 1:
            abort(403, description="Admin privileges required")
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# -----------------------------
# API endpoints
# -----------------------------

@app.route('/products', methods=['GET'])
def list_products():
    """List all products."""
    db = get_db()
    cur = db.execute("SELECT * FROM products")
    products = [dict(row) for row in cur.fetchall()]
    return jsonify(products)

@app.route('/products', methods=['POST'])
@admin_required
def add_product():
    """Add a new product. Admin only."""
    data = request.get_json()
    if not data or 'name' not in data or 'price' not in data:
        abort(400, description="Missing required product fields")
    name = data['name']
    description = data.get('description', '')
    price = data['price']
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
    db.commit()
    product_id = cursor.lastrowid
    return jsonify({"message": "Product added", "product_id": product_id}), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
def modify_product(product_id):
    """Modify product details. Admin only."""
    data = request.get_json()
    if not data:
        abort(400, description="No data provided for update")
    
    db = get_db()
    # Check if product exists
    cur = db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()
    if not product:
        abort(404, description="Product not found")
    
    # Use existing values if not provided in update
    name = data.get('name', product['name'])
    description = data.get('description', product['description'])
    price = data.get('price', product['price'])
    
    db.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?",
               (name, description, price, product_id))
    db.commit()
    return jsonify({"message": "Product updated"})

@app.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    """Remove a product. Admin only."""
    db = get_db()
    cur = db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()
    if not product:
        abort(404, description="Product not found")
    
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return jsonify({"message": "Product deleted"})

# -----------------------------
# Testing route to verify admin user details
# -----------------------------
@app.route('/current_user', methods=['GET'])
def current_user():
    """Return the details of the current user."""
    user = get_current_user()
    return jsonify(dict(user))

# -----------------------------
# Main entry point
# -----------------------------
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
