from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def init_db():
    """Initialize (or reinitialize) the database: create tables and seed sample data."""
    # Remove existing database file if it exists
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Create a users table (with an is_admin flag: 1 for admin, 0 for non-admin)
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            is_admin INTEGER NOT NULL
        )
    ''')
    
    # Create a products table
    c.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    
    # Insert sample users: one admin and one regular user
    c.execute("INSERT INTO users (username, is_admin) VALUES ('admin', 1)")
    c.execute("INSERT INTO users (username, is_admin) VALUES ('user', 0)")
    
    # Insert some sample products
    c.execute("INSERT INTO products (name, description, price) VALUES ('Product A', 'Description A', 10.99)")
    c.execute("INSERT INTO products (name, description, price) VALUES ('Product B', 'Description B', 15.50)")
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Helper to get a database connection with row access by name."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def is_admin(user_id):
    """Check if the given user_id belongs to an admin user."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user is not None and user['is_admin'] == 1

@app.route('/products', methods=['GET'])
def list_products():
    """List all products."""
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return jsonify([dict(prod) for prod in products])

@app.route('/products', methods=['POST'])
def add_product():
    """Add a new product (admin only)."""
    user_id = request.args.get('user_id')
    if not user_id or not user_id.isdigit():
        return jsonify({"error": "Missing or invalid user_id"}), 400
    if not is_admin(int(user_id)):
        return jsonify({"error": "Unauthorized: Admin privileges required"}), 403

    data = request.get_json()
    if not data or not all(k in data for k in ("name", "description", "price")):
        return jsonify({"error": "Missing product data (name, description, price required)"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
        (data['name'], data['description'], data['price'])
    )
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return jsonify({"message": "Product added", "product_id": new_id}), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update product details (admin only)."""
    user_id = request.args.get('user_id')
    if not user_id or not user_id.isdigit():
        return jsonify({"error": "Missing or invalid user_id"}), 400
    if not is_admin(int(user_id)):
        return jsonify({"error": "Unauthorized: Admin privileges required"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing product data"}), 400

    # Prepare the SQL update dynamically based on provided fields.
    fields = []
    values = []
    for field in ["name", "description", "price"]:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400
    values.append(product_id)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"UPDATE products SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return jsonify({"message": "Product updated"}), 200

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product (admin only)."""
    user_id = request.args.get('user_id')
    if not user_id or not user_id.isdigit():
        return jsonify({"error": "Missing or invalid user_id"}), 400
    if not is_admin(int(user_id)):
        return jsonify({"error": "Unauthorized: Admin privileges required"}), 403

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Product deleted"}), 200

@app.route('/reset', methods=['POST'])
def reset_db():
    """
    Endpoint to reset the database to its initial state.
    Useful for testing.
    """
    init_db()
    return jsonify({"message": "Database reset"}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
