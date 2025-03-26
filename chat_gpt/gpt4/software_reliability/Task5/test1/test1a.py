from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Helper function to get a database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Function to initialize the database
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        
        # Create users table
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL,
                            is_admin BOOLEAN NOT NULL)''')
        # Create products table
        cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            description TEXT,
                            price REAL NOT NULL)''')
        # Insert sample data
        cursor.execute("INSERT INTO users (username, is_admin) VALUES ('admin', 1), ('user', 0)")
        cursor.execute("INSERT INTO products (name, description, price) VALUES ('Sample Product', 'This is a sample product.', 9.99)")
        db.commit()

# Close the database connection at the end of the request
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Middleware to verify if the user is an admin
def admin_required(f):
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('User-ID')
        if not user_id:
            return jsonify({"error": "User-ID header is required"}), 400
        # Check if the user is an admin
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        if result is None or result[0] == 0:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Route to add a new product
@app.route('/products', methods=['POST'])
@admin_required
def add_product():
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    price = data.get('price')

    if not name or not price:
        return jsonify({"error": "Product name and price are required"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
    db.commit()
    return jsonify({"message": "Product added successfully"}), 201

# Route to modify an existing product
@app.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
def modify_product(product_id):
    data = request.json
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    if cursor.fetchone() is None:
        return jsonify({"error": "Product not found"}), 404

    cursor.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?",
                   (name, description, price, product_id))
    db.commit()
    return jsonify({"message": "Product updated successfully"}), 200

# Route to delete a product
@app.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return jsonify({"message": "Product deleted successfully"}), 200

# Route to get all products
@app.route('/products', methods=['GET'])
def get_products():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, description, price FROM products")
    products = cursor.fetchall()
    product_list = [{"id": row[0], "name": row[1], "description": row[2], "price": row[3]} for row in products]
    return jsonify(product_list), 200

# Initialize the database before the first request
@app.before_first_request
def setup():
    init_db()

# Start the Flask application
if __name__ == '__main__':
    app.run(debug=True)