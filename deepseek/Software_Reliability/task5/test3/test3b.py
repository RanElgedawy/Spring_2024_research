from flask import Flask, request, jsonify
import sqlite3
from functools import wraps

app = Flask(__name__)

# Database initialization
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    
    # Create users table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, 
                  username TEXT UNIQUE, 
                  is_admin BOOLEAN)''')
    
    # Create products table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY,
                  name TEXT,
                  price REAL,
                  description TEXT,
                  stock INTEGER)''')
    
    conn.commit()
    conn.close()

init_db()

# Decorator to check admin privileges
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.args.get('user_id')
        if not is_admin(user_id):
            return jsonify({"error": "Admin privileges required"}), 403
        return f(*args, **kwargs)
    return decorated_function

def is_admin(user_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0]

# Product management endpoints
@app.route('/product', methods=['POST'])
@admin_required
def add_product():
    data = request.get_json()
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''INSERT INTO products (name, price, description, stock)
                 VALUES (?, ?, ?, ?)''',
              (data['name'], data['price'], data['description'], data['stock']))
    product_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"message": "Product added", "product_id": product_id}), 201

@app.route('/product/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    data = request.get_json()
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''UPDATE products SET 
                 name = ?, price = ?, description = ?, stock = ?
                 WHERE id = ?''',
              (data['name'], data['price'], data['description'], 
               data['stock'], product_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Product updated"}), 200

@app.route('/product/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Product deleted"}), 200

# Testing function
def test_system():
    # Initialize test database
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    # Create test users
    c.execute("INSERT INTO users (username, is_admin) VALUES ('admin', 1)")
    c.execute("INSERT INTO users (username, is_admin) VALUES ('user', 0)")
    conn.commit()
    conn.close()

    # Test admin operations
    print("Testing admin operations:")
    with app.test_client() as client:
        # Admin user (id=1)
        response = client.post('/product?user_id=1', json={
            'name': 'Test Product',
            'price': 19.99,
            'description': 'Test Description',
            'stock': 100
        })
        print("Add product (admin):", response.status_code, response.json)

        # Regular user (id=2)
        response = client.post('/product?user_id=2', json={
            'name': 'Unauthorized Product',
            'price': 9.99,
            'description': 'Should fail',
            'stock': 10
        })
        print("Add product (non-admin):", response.status_code)

if __name__ == '__main__':
    init_db()
    test_system()
    app.run(debug=True)