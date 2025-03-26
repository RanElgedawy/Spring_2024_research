from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db():
    """Get a database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with users and products tables."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                is_admin INTEGER NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        ''')
        db.commit()

@app.before_first_request
def initialize_data():
    """Initialize the database with some test data."""
    init_db()
    db = get_db()
    cursor = db.cursor()
    
    # Insert test users (one admin and one non-admin)
    cursor.execute('INSERT OR IGNORE INTO users (username, is_admin) VALUES (?, ?)', ('admin_user', 1))
    cursor.execute('INSERT OR IGNORE INTO users (username, is_admin) VALUES (?, ?)', ('regular_user', 0))
    
    # Insert test products
    cursor.execute('INSERT OR IGNORE INTO products (name, description, price) VALUES (?, ?, ?)', ('Sample Product', 'This is a sample product.', 19.99))
    
    db.commit()

def is_admin(username):
    """Check if the given user is an admin."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    return result is not None and result[0] == 1

@app.route('/products', methods=['GET'])
def list_products():
    """List all products."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    return jsonify(products)

@app.route('/products', methods=['POST'])
def add_product():
    """Add a new product (Admin only)."""
    username = request.headers.get('Username')
    if not is_admin(username):
        return jsonify({'error': 'Unauthorized access'}), 403
    
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    price = data.get('price')
    
    if not name or price is None:
        return jsonify({'error': 'Name and price are required'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
    db.commit()
    return jsonify({'message': 'Product added successfully'}), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update an existing product (Admin only)."""
    username = request.headers.get('Username')
    if not is_admin(username):
        return jsonify({'error': 'Unauthorized access'}), 403
    
    data = request.json
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    
    if not name or price is None:
        return jsonify({'error': 'Name and price are required'}), 400
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?', (name, description, price, product_id))
    db.commit()
    return jsonify({'message': 'Product updated successfully'})

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product (Admin only)."""
    username = request.headers.get('Username')
    if not is_admin(username):
        return jsonify({'error': 'Unauthorized access'}), 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()
    return jsonify({'message': 'Product deleted successfully'})

if __name__ == '__main__':
    # Initialize the database and run the Flask app
    init_db()
    app.run(debug=True)