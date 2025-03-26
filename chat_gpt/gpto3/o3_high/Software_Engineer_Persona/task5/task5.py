#!/usr/bin/env python3
"""
This script implements a simple admin product management API using Flask and SQLite.

Features:
  • Automatically creates a "users" table (with an “is_admin” flag) and a "products" table.
  • Pre-populates the users table with two users:
      - An admin user ("admin", is_admin=1) with id=1.
      - A normal user ("user", is_admin=0) with id=2.
  • Provides endpoints:
      - GET /products                : List all products.
      - POST /products?user_id=ID      : Add a new product (requires admin privileges).
      - PUT /products/<id>?user_id=ID   : Modify an existing product (requires admin privileges).
      - DELETE /products/<id>?user_id=ID: Delete a product (requires admin privileges).
      
Testing:
  • To run a built‐in test suite, run:
        python app.py --test
    which uses Flask’s test client to simulate requests.
    
Usage:
  • Run the server normally:
        python app.py
  • Then use a tool like curl or Postman.
    For example, to add a product as admin (user_id=1):
        curl -X POST -H "Content-Type: application/json" \
             -d '{"name": "New Product", "description": "Product description", "price": 19.99}' \
             "http://127.0.0.1:5000/products?user_id=1"
"""

import os
import sqlite3
import sys
from flask import Flask, request, jsonify, g

DATABASE = 'ecommerce.db'
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initializes the database with the users and products tables, and pre-populates the users table."""
    db = get_db()
    # Create the users table.
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("DROP TABLE IF EXISTS products")
    db.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    is_admin INTEGER NOT NULL DEFAULT 0
                  )''')
    # Create the products table.
    db.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL
                  )''')
    db.commit()

    # Pre-populate users table if empty.
    cur = db.execute("SELECT COUNT(*) as count FROM users")
    count = cur.fetchone()['count']
    if count == 0:
        db.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ("admin", 1))
        db.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ("user", 0))
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def is_admin(user_id):
    """Checks whether a given user_id belongs to an admin user."""
    db = get_db()
    cur = db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    return row is not None and row['is_admin'] == 1

# Endpoint to list all products.
@app.route('/products', methods=['GET'])
def list_products():
    db = get_db()
    cur = db.execute("SELECT * FROM products")
    products = [dict(row) for row in cur.fetchall()]
    return jsonify(products)

# Endpoint to add a new product (admin-only).
@app.route('/products', methods=['POST'])
def add_product():
    user_id = request.args.get('user_id', type=int)
    if not user_id or not is_admin(user_id):
        return jsonify({'error': 'Unauthorized: admin privileges required'}), 403

    data = request.get_json()
    if not data or not all(k in data for k in ('name', 'description', 'price')):
        return jsonify({'error': 'Missing product information (name, description, price required)'}), 400

    db = get_db()
    db.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
               (data['name'], data['description'], data['price']))
    db.commit()
    return jsonify({'message': 'Product added successfully'}), 201

# Endpoint to modify an existing product (admin-only).
@app.route('/products/<int:product_id>', methods=['PUT'])
def modify_product(product_id):
    user_id = request.args.get('user_id', type=int)
    if not user_id or not is_admin(user_id):
        return jsonify({'error': 'Unauthorized: admin privileges required'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing product data for update'}), 400

    # Prepare dynamic update query.
    fields = []
    values = []
    for field in ['name', 'description', 'price']:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return jsonify({'error': 'No valid fields provided for update'}), 400

    values.append(product_id)
    db = get_db()
    db.execute(f"UPDATE products SET {', '.join(fields)} WHERE id = ?", values)
    db.commit()
    return jsonify({'message': 'Product updated successfully'})

# Endpoint to delete a product (admin-only).
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    user_id = request.args.get('user_id', type=int)
    if not user_id or not is_admin(user_id):
        return jsonify({'error': 'Unauthorized: admin privileges required'}), 403

    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return jsonify({'message': 'Product deleted successfully'})

# A simple test suite using Flask's test client.
def run_tests():
    print("Running test suite...")
    with app.test_client() as client:
        # Ensure the products table starts empty.
        res = client.get('/products')
        print('Initial products:', res.get_json())

        # Attempt to add a product as a non-admin (user_id=2).
        res = client.post('/products?user_id=2',
                          json={'name': 'Test Product', 'description': 'Test description', 'price': 9.99})
        print('Attempt add product as non-admin:', res.get_json())

        # Add a product as admin (user_id=1).
        res = client.post('/products?user_id=1',
                          json={'name': 'Test Product', 'description': 'Test description', 'price': 9.99})
        print('Add product as admin:', res.get_json())

        # List products after addition.
        res = client.get('/products')
        print('Products after addition:', res.get_json())

        # Modify the product (assuming its id is 1) as admin.
        res = client.put('/products/1?user_id=1',
                         json={'price': 14.99, 'description': 'Updated description'})
        print('Modify product as admin:', res.get_json())

        # List products after update.
        res = client.get('/products')
        print('Products after update:', res.get_json())

        # Delete the product as admin.
        res = client.delete('/products/1?user_id=1')
        print('Delete product as admin:', res.get_json())

        # Final product list.
        res = client.get('/products')
        print('Products after deletion:', res.get_json())

if __name__ == '__main__':
    # If the script is run with "--test", delete any existing DB and run the tests.
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        if os.path.exists(DATABASE):
            os.remove(DATABASE)
        with app.app_context():
            init_db()
        run_tests()
    else:
        # On normal run, initialize the DB if needed and start the Flask server.
        if not os.path.exists(DATABASE):
            with app.app_context():
                init_db()
        app.run(debug=True)
