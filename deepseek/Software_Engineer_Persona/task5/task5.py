from flask import Flask, request, jsonify, session
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production
DATABASE = 'ecommerce.db'

# Database initialization
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")

    c.execute("DROP TABLE IF EXISTS products")
    
    # Create users table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  is_admin BOOLEAN DEFAULT 0)''')
    
    # Create products table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  price REAL,
                  description TEXT,
                  stock INTEGER)''')
    
    conn.commit()
    conn.close()

# Database helper functions
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

# Decorator for admin verification
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user['is_admin']:
            return jsonify({"error": "Admin privileges required"}), 403
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    # In a real app, this would retrieve the logged-in user from the session
    # For simplicity, we'll assume the user is logged in and retrieve from db
    # Here, we'll simulate by using a default user (admin)
    return get_user_by_id(0)

# Product management endpoints
@app.route('/products', methods=['POST'])
@admin_required
def add_product():
    data = request.get_json()
    required_fields = ['name', 'price', 'description', 'stock']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO products (name, price, description, stock)
                 VALUES (?, ?, ?, ?)''',
              (data['name'], data['price'], data['description'], data['stock']))
    product_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Product added", "product_id": product_id}), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    data = request.get_json()
    conn = get_db()
    c = conn.cursor()
    
    # Check for fields to update
    updates = []
    params = []
    for field in ['name', 'price', 'description', 'stock']:
        if field in data:
            updates.append(f"{field} = ?")
            params.append(data[field])
    
    if not updates:
        conn.close()
        return jsonify({"error": "No fields to update"}), 400
    
    # Verify product exists
    c.execute('SELECT id FROM products WHERE id = ?', (product_id,))
    if not c.fetchone():
        conn.close()
        return jsonify({"error": "Product not found"}), 404
    
    # Perform update
    params.append(product_id)
    c.execute(f'''UPDATE products SET {', '.join(updates)} 
               WHERE id = ?''', params)
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Product updated"})

@app.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    conn = get_db()
    c = conn.cursor()
    
    # Verify product exists first
    c.execute('SELECT id FROM products WHERE id = ?', (product_id,))
    if not c.fetchone():
        conn.close()
        return jsonify({"error": "Product not found"}), 404
    
    # Perform deletion
    c.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Product deleted"})

# Test setup endpoint
@app.route('/test_setup', methods=['POST'])
def test_setup():
    conn = get_db()
    c = conn.cursor()

    # Create test admin user
    c.execute('''INSERT OR IGNORE INTO users (username, password, is_admin)
                 VALUES (?, ?, ?)''', 
              ('admin@test.com', 'test123', 1))
    
    # Create test normal user
    c.execute('''INSERT OR IGNORE INTO users (username, password, is_admin)
                 VALUES (?, ?, ?)''', 
              ('user@test.com', 'test123', 0))
    
    # Create test product
    c.execute('''INSERT OR IGNORE INTO products (name, price, description, stock)
                 VALUES (?, ?, ?, ?)''',
              ('Test Product', 99.99, 'Test Description', 100))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Test data initialized"})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)