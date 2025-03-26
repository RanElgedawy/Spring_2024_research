from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)

DATABASE = 'ecommerce.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
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
                username TEXT NOT NULL UNIQUE,
                is_admin BOOLEAN NOT NULL
            )
        ''')
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        ''')
        # Insert a sample admin user and a regular user
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, is_admin) VALUES
            ('admin_user', 1),
            ('regular_user', 0)
        ''')
        db.commit()

# Utility function to check if a user is an admin
def is_admin_user(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    return result is not None and result[0] == 1

# Route to add a new product (admin only)
@app.route('/add_product', methods=['POST'])
def add_product():
    username = request.headers.get('Username')
    if not is_admin_user(username):
        return jsonify({"error": "Unauthorized access. Admin privileges required."}), 403

    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    price = data.get('price')
    stock = data.get('stock')

    if not name or price is None or stock is None:
        return jsonify({"error": "Missing required product fields"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)',
                   (name, description, price, stock))
    db.commit()
    return jsonify({"message": "Product added successfully"}), 201

# Route to modify an existing product (admin only)
@app.route('/modify_product/<int:product_id>', methods=['PUT'])
def modify_product(product_id):
    username = request.headers.get('Username')
    if not is_admin_user(username):
        return jsonify({"error": "Unauthorized access. Admin privileges required."}), 403

    data = request.json
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock')

    if not any([name, description, price, stock]):
        return jsonify({"error": "No fields to update"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    if cursor.fetchone() is None:
        return jsonify({"error": "Product not found"}), 404

    update_fields = []
    values = []
    if name:
        update_fields.append('name = ?')
        values.append(name)
    if description:
        update_fields.append('description = ?')
        values.append(description)
    if price is not None:
        update_fields.append('price = ?')
        values.append(price)
    if stock is not None:
        update_fields.append('stock = ?')
        values.append(stock)

    values.append(product_id)
    cursor.execute(f'UPDATE products SET {", ".join(update_fields)} WHERE id = ?', values)
    db.commit()
    return jsonify({"message": "Product updated successfully"}), 200

# Route to delete a product (admin only)
@app.route('/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    username = request.headers.get('Username')
    if not is_admin_user(username):
        return jsonify({"error": "Unauthorized access. Admin privileges required."}), 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    if cursor.fetchone() is None:
        return jsonify({"error": "Product not found"}), 404

    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()
    return jsonify({"message": "Product deleted successfully"}), 200

# Route to list all products (accessible to all users)
@app.route('/list_products', methods=['GET'])
def list_products():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    return jsonify({"products": products})

# Initialize the database
init_db()

if __name__ == '__main__':
    app.run(debug=True)