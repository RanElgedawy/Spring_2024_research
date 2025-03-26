from flask import Flask, request, jsonify, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)

# Database setup
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
        # Create tables
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                is_admin BOOLEAN NOT NULL CHECK (is_admin IN (0, 1))
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

# Route to add a user (for testing)
@app.route('/add_user', methods=['POST'])
def add_user():
    db = get_db()
    cursor = db.cursor()
    username = request.json['username']
    password = generate_password_hash(request.json['password'])
    is_admin = request.json['is_admin']
    
    cursor.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                   (username, password, is_admin))
    db.commit()
    return jsonify({"message": "User added successfully"}), 201

# Function to verify admin privileges
def is_admin(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    return user is not None and user[0] == 1

# Route to add a product
@app.route('/products', methods=['POST'])
def add_product():
    user_id = request.json['user_id']
    if not is_admin(user_id):
        return jsonify({"error": "Admin access required"}), 403
    
    db = get_db()
    cursor = db.cursor()
    name = request.json['name']
    description = request.json.get('description', '')
    price = request.json['price']
    
    cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                   (name, description, price))
    db.commit()
    return jsonify({"message": "Product added successfully"}), 201

# Route to update a product
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    user_id = request.json['user_id']
    if not is_admin(user_id):
        return jsonify({"error": "Admin access required"}), 403
    
    db = get_db()
    cursor = db.cursor()

    # Check if the product exists
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    # Update the product if it exists
    name = request.json['name']
    description = request.json.get('description', '')
    price = request.json['price']
    
    cursor.execute('''
        UPDATE products 
        SET name = ?, description = ?, price = ? 
        WHERE id = ?
    ''', (name, description, price, product_id))
    db.commit()
    
    return jsonify({"message": "Product updated successfully"}), 200

# Route to delete a product
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    user_id = request.json['user_id']
    if not is_admin(user_id):
        return jsonify({"error": "Admin access required"}), 403
    
    db = get_db()
    cursor = db.cursor()

    # Check if the product exists
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    # Delete the product if it exists
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()
    
    return jsonify({"message": "Product deleted successfully"}), 200

# Route to view products (no admin check)
@app.route('/products', methods=['GET'])
def view_products():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    return jsonify(products)

# Initialize the database
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
