from flask import Flask, request, jsonify, g, abort
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Remove existing database for a clean slate (optional)
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS products")

    # Create users table with an admin flag
    cur.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            is_admin INTEGER NOT NULL DEFAULT 0
        );
    ''')
    
    # Create products table
    cur.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        );
    ''')
    
    # Insert sample users (user 1: admin, user 2: non-admin)
    cur.execute('INSERT INTO users (username, is_admin) VALUES (?, ?)', ("admin_user", 1))
    cur.execute('INSERT INTO users (username, is_admin) VALUES (?, ?)', ("regular_user", 0))
    
    # Insert a sample product
    cur.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', 
                ("Sample Product", "This is a sample product.", 19.99))
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def admin_required(func):
    """Decorator to check if the user is admin.
       Expects a query parameter 'user_id' in the request.
    """
    def wrapper(*args, **kwargs):
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            abort(400, description="Missing user_id parameter.")
        user = get_user(user_id)
        if not user:
            abort(404, description="User not found.")
        if not user['is_admin']:
            abort(403, description="Admin privileges required.")
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route('/products', methods=['GET'])
def list_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    # Convert rows to dicts
    product_list = [dict(prod) for prod in products]
    return jsonify(product_list)

@app.route('/products', methods=['POST'])
@admin_required
def add_product():
    data = request.get_json()
    if not data or not all(k in data for k in ("name", "price")):
        abort(400, description="Missing product name or price.")
    
    name = data["name"]
    description = data.get("description", "")
    price = data["price"]
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    
    return jsonify({"message": "Product added", "product_id": new_id}), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    data = request.get_json()
    if not data:
        abort(400, description="No update data provided.")
    
    # Build a dynamic query based on provided fields.
    fields = []
    values = []
    for field in ["name", "description", "price"]:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    
    if not fields:
        abort(400, description="No valid fields to update.")
    
    values.append(product_id)
    query = f"UPDATE products SET {', '.join(fields)} WHERE id = ?"
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, tuple(values))
    if cur.rowcount == 0:
        conn.close()
        abort(404, description="Product not found.")
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Product updated"})

@app.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    if cur.rowcount == 0:
        conn.close()
        abort(404, description="Product not found.")
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Product deleted"})

if __name__ == '__main__':
    init_db()
    print("Database initialized with sample data.")
    print("Admin user id: 1 (admin_user), Regular user id: 2 (regular_user)")
    app.run(debug=True)
