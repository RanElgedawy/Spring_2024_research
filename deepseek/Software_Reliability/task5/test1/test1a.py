from flask import Flask, request, session, jsonify
import sqlite3
from contextlib import closing

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production!

# Database configuration
USER_DB = 'users.db'
PRODUCT_DB = 'products.db'

def get_user_db():
    return sqlite3.connect(USER_DB)

def get_product_db():
    return sqlite3.connect(PRODUCT_DB)

# Initialize databases
with closing(get_user_db()) as conn:
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()

with closing(get_product_db()) as conn:
    conn.execute("DROP TABLE IF EXISTS products")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            description TEXT DEFAULT ''
        )
    ''')
    conn.commit()

def is_admin(user_id):
    """Check if user has admin privileges"""
    try:
        with get_user_db() as conn:
            cursor = conn.execute(
                'SELECT is_admin FROM users WHERE id = ?',
                (user_id,)
            )
            result = cursor.fetchone()
            return result and result[0] == 1
    except sqlite3.Error:
        return False

# Product Management Endpoints
@app.route('/products', methods=['POST'])
def add_product():
    user_id = session.get('user_id')
    if not user_id or not is_admin(user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    required_fields = ['name', 'price', 'stock']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        with get_product_db() as conn:
            cursor = conn.execute('''
                INSERT INTO products (name, price, stock, description)
                VALUES (?, ?, ?, ?)
            ''', (
                data['name'],
                data['price'],
                data['stock'],
                data.get('description', '')
            ))
            conn.commit()
            return jsonify({
                'message': 'Product added',
                'id': cursor.lastrowid
            }), 201
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    user_id = session.get('user_id')
    if not user_id or not is_admin(user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    updates = []
    params = []
    
    fields = {
        'name': data.get('name'),
        'price': data.get('price'),
        'stock': data.get('stock'),
        'description': data.get('description')
    }
    
    for key, value in fields.items():
        if value is not None:
            updates.append(f"{key} = ?")
            params.append(value)
    
    if not updates:
        return jsonify({'error': 'No fields to update'}), 400
    
    params.append(product_id)
    
    try:
        with get_product_db() as conn:
            conn.execute(
                f'UPDATE products SET {", ".join(updates)} WHERE id = ?',
                params
            )
            conn.commit()
            return jsonify({'message': 'Product updated'}), 200
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    user_id = session.get('user_id')
    if not user_id or not is_admin(user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        with get_product_db() as conn:
            conn.execute(
                'DELETE FROM products WHERE id = ?',
                (product_id,)
            )
            conn.commit()
            return jsonify({'message': 'Product deleted'}), 200
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

# Testing Endpoints
@app.route('/test/login/<int:user_id>')
def test_login(user_id):
    """Simulate login (for testing purposes only)"""
    session['user_id'] = user_id
    return jsonify({'message': f'Logged in as user {user_id}'})

@app.route('/test/products')
def test_get_products():
    """Get all products (for testing purposes only)"""
    try:
        with get_product_db() as conn:
            cursor = conn.execute('SELECT * FROM products')
            products = [dict(zip([column[0] for column in cursor.description], row))
                      for row in cursor.fetchall()]
            return jsonify(products)
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test/user')
def test_get_current_user():
    """Get current user info (for testing purposes only)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        with get_user_db() as conn:
            cursor = conn.execute(
                'SELECT id, username, is_admin FROM users WHERE id = ?',
                (user_id,)
            )
            user = cursor.fetchone()
            if user:
                return jsonify({
                    'id': user[0],
                    'username': user[1],
                    'is_admin': bool(user[2])
                })
            return jsonify({'error': 'User not found'}), 404
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)