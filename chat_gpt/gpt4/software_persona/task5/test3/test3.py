from flask import Flask, request, jsonify, g, redirect, url_for
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Utility function to get the database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Function to initialize the database with the schema directly in the code
def init_db():
    db = get_db()
    schema = '''
    DROP TABLE IF EXISTS users;
    
    DROP TABLE IF EXISTS products;

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        is_admin INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    );
    '''
    db.executescript(schema)
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Verify if the user is an admin
def is_admin(user_id):
    cur = get_db().execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    return user and user[0] == 1

# Route to add a new product (admin only)
@app.route('/product/add', methods=['POST'])
def add_product():
    user_id = request.json.get('user_id')
    if not is_admin(user_id):
        return jsonify({"error": "Access denied"}), 403

    name = request.json.get('name')
    description = request.json.get('description')
    price = request.json.get('price')

    db = get_db()
    db.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', 
               (name, description, price))
    db.commit()

    return jsonify({"success": "Product added"}), 201

# Route to modify an existing product (admin only)
@app.route('/product/edit/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    user_id = request.json.get('user_id')
    if not is_admin(user_id):
        return jsonify({"error": "Access denied"}), 403

    db = get_db()

    # Check if the product exists
    cur = db.execute('SELECT id FROM products WHERE id = ?', (product_id,))
    product = cur.fetchone()

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    # Get the updated product details from the request
    name = request.json.get('name')
    description = request.json.get('description')
    price = request.json.get('price')

    # Update the product details
    db.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?', 
               (name, description, price, product_id))
    db.commit()

    return jsonify({"success": "Product updated"}), 200

# Route to delete a product (admin only)
@app.route('/product/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    user_id = request.json.get('user_id')
    if not is_admin(user_id):
        return jsonify({"error": "Access denied"}), 403

    db = get_db()
    
    # Check if the product exists
    cur = db.execute('SELECT id FROM products WHERE id = ?', (product_id,))
    product = cur.fetchone()
    
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    # Delete the product
    db.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()

    return jsonify({"success": "Product deleted"}), 200

# Route to initialize the database (for testing purposes)
@app.route('/initdb', methods=['GET'])
def initialize_database():
    init_db()
    return "Database initialized!"

# Sample data for testing
@app.route('/testdata', methods=['GET'])
def test_data():
    db = get_db()
    db.execute('INSERT INTO users (username, is_admin) VALUES (?, ?)', ('admin_user', 1))
    db.execute('INSERT INTO users (username, is_admin) VALUES (?, ?)', ('normal_user', 0))
    db.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', 
               ('Sample Product', 'This is a sample product.', 9.99))
    db.commit()
    return "Test data added!"

if __name__ == '__main__':
    app.run(debug=True)