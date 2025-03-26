from flask import Flask, request, jsonify, g
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Database setup
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT 0
            )
        ''')
        
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                stock INTEGER NOT NULL
            )
        ''')
        
        # Insert sample admin user if not exists
        cursor.execute('INSERT OR IGNORE INTO users (username, is_admin) VALUES (?, ?)', 
                      ('admin@example.com', 1))
        # Insert sample regular user
        cursor.execute('INSERT OR IGNORE INTO users (username, is_admin) VALUES (?, ?)', 
                      ('user@example.com', 0))
        db.commit()

# Admin check middleware
def check_admin(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    return user and user['is_admin'] == 1

# Product CRUD operations
@app.route('/products', methods=['POST'])
def add_product():
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not check_admin(user_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('''
            INSERT INTO products (name, price, description, stock)
            VALUES (?, ?, ?, ?)
        ''', (data['name'], data['price'], data.get('description'), data['stock']))
        db.commit()
        return jsonify({'message': 'Product added', 'product_id': cursor.lastrowid}), 201
    except sqlite3.IntegrityError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not check_admin(user_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('''
            UPDATE products 
            SET name = ?, price = ?, description = ?, stock = ?
            WHERE id = ?
        ''', (data['name'], data['price'], data.get('description'), data['stock'], product_id))
        db.commit()
        return jsonify({'message': 'Product updated'}), 200
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    user_id = request.args.get('user_id')
    
    if not check_admin(user_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()
    return jsonify({'message': 'Product deleted'}), 200

# Test routes
@app.route('/test/setup')
def test_setup():
    init_db()
    return jsonify({'message': 'Database initialized with test data'})

@app.route('/test/products')
def test_get_products():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products')
    products = [dict(row) for row in cursor.fetchall()]
    return jsonify(products)

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)