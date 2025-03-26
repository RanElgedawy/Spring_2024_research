from flask import Flask, request, jsonify, g
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # enables column access by name
    return db

def init_db():
    """Create tables if they do not already exist."""
    db = get_db()
    cursor = db.cursor()
    # Create a simple users table (for testing)
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS carts")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL
        )
    ''')
    # Create products table with stock information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    # Create carts table that links users and products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    db.commit()

def seed_db():
    """Seed the database with sample data if no data exists."""
    db = get_db()
    cursor = db.cursor()
    # Insert a sample user if none exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, email) VALUES (?, ?)", 
                       ("testuser", "test@example.com"))
    # Insert sample products if none exist
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        products = [
            ("Widget", 19.99, 100),
            ("Gadget", 29.99, 50),
            ("Doodad", 9.99, 200)
        ]
        for name, price, stock in products:
            cursor.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
                           (name, price, stock))
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/api/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Retrieve product information by product ID."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    # Convert row to a dictionary
    return jsonify(dict(product))

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """
    Add a product to a user's cart.
    Expects JSON with: user_id, product_id, and quantity (default is 1).
    Only adds the product if it exists, the user exists, and sufficient stock is available.
    Uses parameterized queries to mitigate SQL injection.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    user_id = data.get('user_id')
    product_id = data.get('product_id')
    try:
        quantity = int(data.get('quantity', 1))
    except (ValueError, TypeError):
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    if not user_id or not product_id or quantity <= 0:
        return jsonify({"error": "Missing or invalid parameters"}), 400

    db = get_db()
    cursor = db.cursor()

    # Validate user exists
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Validate product exists and check stock
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({"error": "Product not found"}), 404

    available_stock = product['stock']
    if available_stock < quantity:
        return jsonify({"error": "Not enough stock available"}), 400

    # Add product to cart using a parameterized query
    cursor.execute("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
                   (user_id, product_id, quantity))
    # Update product stock securely
    cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                   (quantity, product_id))
    db.commit()

    return jsonify({"message": "Product added to cart successfully"}), 200

if __name__ == '__main__':
    # Initialize and seed the database when running the app
    with app.app_context():
        init_db()
        seed_db()
    # Run the app (debug mode can be turned off in production)
    app.run(debug=True)
