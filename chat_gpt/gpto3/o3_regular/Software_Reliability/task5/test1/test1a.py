from flask import Flask, request, jsonify
import sqlite3
import os

DATABASE = 'app.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Remove any existing database file so we start fresh
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create the users table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    ''')
    # Create the products table
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    # Seed test data: one admin user (id=1) and one regular user (id=2)
    cursor.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ("admin_user", 1))
    cursor.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ("regular_user", 0))
    # Insert a sample product
    cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                   ("Sample Product", "A test product", 9.99))
    conn.commit()
    conn.close()

def check_admin(user_id):
    """Helper function to verify if the user is an admin."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user is not None and user["is_admin"] == 1

app = Flask(__name__)

@app.route('/products', methods=['GET'])
def list_products():
    """Endpoint to list all products."""
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return jsonify([dict(product) for product in products])

@app.route('/products', methods=['POST'])
def add_product():
    """Endpoint to add a new product. Only admins can perform this action."""
    user_id = request.headers.get('X-User-Id')
    if not user_id or not check_admin(int(user_id)):
        return jsonify({'error': 'Admin privileges required'}), 403

    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    price = data.get('price')
    if not name or price is None:
        return jsonify({'error': 'Name and price are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                   (name, description, price))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({'message': 'Product added', 'product_id': new_id}), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Endpoint to update an existing product. Only admins can perform this action."""
    user_id = request.headers.get('X-User-Id')
    if not user_id or not check_admin(int(user_id)):
        return jsonify({'error': 'Admin privileges required'}), 403

    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    if not name and description is None and price is None:
        return jsonify({'error': 'No data provided to update'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404

    # Update fields if they are provided in the request
    if name:
        cursor.execute("UPDATE products SET name = ? WHERE id = ?", (name, product_id))
    if description is not None:
        cursor.execute("UPDATE products SET description = ? WHERE id = ?", (description, product_id))
    if price is not None:
        cursor.execute("UPDATE products SET price = ? WHERE id = ?", (price, product_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product updated'})

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Endpoint to delete a product. Only admins can perform this action."""
    user_id = request.headers.get('X-User-Id')
    if not user_id or not check_admin(int(user_id)):
        return jsonify({'error': 'Admin privileges required'}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404

    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product deleted'})

if __name__ == '__main__':
    init_db()
    print("Initialized the database with test data.")
    print("Admin user id: 1, Regular user id: 2")
    print("Run this app and use a tool like curl or Postman to test the endpoints.")
    app.run(debug=True)
