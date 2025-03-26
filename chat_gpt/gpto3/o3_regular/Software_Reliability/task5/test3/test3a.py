import sqlite3
from flask import Flask, request, jsonify, g

DATABASE = 'ecommerce.db'
app = Flask(__name__)

def get_db():
    """Retrieve the database connection for the current request."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection after each request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with the required tables and seed data."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create a users table
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            )
        ''')
        # Create a products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT
            )
        ''')
        # Clear existing data for testing purposes
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM products")
        # Seed users: one admin and one non-admin
        cursor.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ('admin', 1))
        cursor.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ('user', 0))
        # Seed a sample product
        cursor.execute("INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
                       ('Sample Product', 9.99, 'This is a sample product.'))
        db.commit()

def check_admin(user_id):
    """Verify if the given user_id belongs to an admin user."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    return row and row['is_admin'] == 1

@app.route('/products', methods=['GET'])
def get_products():
    """List all products."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products")
    products = [dict(row) for row in cursor.fetchall()]
    return jsonify(products)

@app.route('/products', methods=['POST'])
def add_product():
    """Add a new product (admin only)."""
    user_id = request.headers.get('User-ID')
    if not user_id or not check_admin(user_id):
        return jsonify({'error': 'Admin privileges required.'}), 403

    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    description = data.get('description', '')
    if not name or price is None:
        return jsonify({'error': 'Name and price are required.'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
                   (name, price, description))
    db.commit()
    product_id = cursor.lastrowid
    return jsonify({'message': 'Product added successfully.', 'product_id': product_id}), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update an existing product (admin only)."""
    user_id = request.headers.get('User-ID')
    if not user_id or not check_admin(user_id):
        return jsonify({'error': 'Admin privileges required.'}), 403

    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    description = data.get('description')

    db = get_db()
    cursor = db.cursor()
    # Check if product exists
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    if not cursor.fetchone():
        return jsonify({'error': 'Product not found.'}), 404

    # Update provided fields
    if name:
        cursor.execute("UPDATE products SET name = ? WHERE id = ?", (name, product_id))
    if price is not None:
        cursor.execute("UPDATE products SET price = ? WHERE id = ?", (price, product_id))
    if description is not None:
        cursor.execute("UPDATE products SET description = ? WHERE id = ?", (description, product_id))
    db.commit()
    return jsonify({'message': 'Product updated successfully.'})

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product (admin only)."""
    user_id = request.headers.get('User-ID')
    if not user_id or not check_admin(user_id):
        return jsonify({'error': 'Admin privileges required.'}), 403

    db = get_db()
    cursor = db.cursor()
    # Check if product exists
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    if not cursor.fetchone():
        return jsonify({'error': 'Product not found.'}), 404

    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return jsonify({'message': 'Product deleted successfully.'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
