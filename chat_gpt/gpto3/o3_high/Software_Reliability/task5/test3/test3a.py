from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()
    # Create users table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL
        )
    ''')
    db.commit()

def seed_data():
    db = get_db()
    cursor = db.cursor()
    # Seed users if table is empty
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        users = [
            (1, 'admin_user', 1),
            (2, 'regular_user', 0)
        ]
        cursor.executemany('INSERT INTO users (id, username, is_admin) VALUES (?, ?, ?)', users)
    # Seed products if table is empty
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        products = [
            (1, 'Widget A', 'A high-quality widget.', 9.99, 100),
            (2, 'Widget B', 'Another useful widget.', 19.99, 50)
        ]
        cursor.executemany('INSERT INTO products (id, name, description, price, quantity) VALUES (?, ?, ?, ?, ?)', products)
    db.commit()

def check_admin(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    return row is not None and row['is_admin'] == 1

@app.route('/admin/product/add', methods=['POST'])
def add_product():
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'error': 'X-User-Id header required'}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid User ID'}), 400

    if not check_admin(user_id):
        return jsonify({'error': 'Unauthorized: Admin access required'}), 403

    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    price = data.get('price')
    quantity = data.get('quantity')

    if not name or price is None or quantity is None:
        return jsonify({'error': 'Missing required fields: name, price, quantity'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO products (name, description, price, quantity) VALUES (?, ?, ?, ?)',
                   (name, description, price, quantity))
    db.commit()
    return jsonify({'message': 'Product added successfully', 'product_id': cursor.lastrowid})

@app.route('/admin/product/update/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'error': 'X-User-Id header required'}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid User ID'}), 400

    if not check_admin(user_id):
        return jsonify({'error': 'Unauthorized: Admin access required'}), 403

    data = request.get_json()
    fields = []
    values = []
    for field in ['name', 'description', 'price', 'quantity']:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return jsonify({'error': 'No valid fields to update'}), 400

    values.append(product_id)
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f'UPDATE products SET {", ".join(fields)} WHERE id = ?', values)
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'message': 'Product updated successfully'})

@app.route('/admin/product/delete/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'error': 'X-User-Id header required'}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid User ID'}), 400

    if not check_admin(user_id):
        return jsonify({'error': 'Unauthorized: Admin access required'}), 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'message': 'Product deleted successfully'})

@app.route('/admin/product/list', methods=['GET'])
def list_products():
    # No admin check required to view products
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products')
    products = [dict(row) for row in cursor.fetchall()]
    return jsonify(products)

if __name__ == '__main__':
    with app.app_context():
        init_db()
        seed_data()
    app.run(debug=True)
