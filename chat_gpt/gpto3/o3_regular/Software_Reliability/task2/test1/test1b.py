from flask import Flask, request, jsonify, g
import sqlite3
import os

DATABASE = "ecommerce.db"

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Connect to SQLite database (will create if it doesn't exist)
        db = g._database = sqlite3.connect(DATABASE)
        # Return rows as dictionaries
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Create tables and insert sample data if they do not already exist."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS carts")
    cursor.execute("DROP TABLE IF EXISTS users")

    # Create a table for products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')

    # Create a table for carts (each row represents an item in a user's cart)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            UNIQUE(user_id, product_id)
        )
    ''')

    # Create a table for users (for demonstration purposes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE
        )
    ''')

    # Insert sample data for products if table is empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ("Widget A", "A useful widget.", 19.99, 10),
            ("Widget B", "Another useful widget.", 29.99, 5),
            ("Widget C", "A limited edition widget.", 39.99, 0)  # out of stock
        ]
        cursor.executemany('''
            INSERT INTO products (name, description, price, stock)
            VALUES (?, ?, ?, ?)
        ''', sample_products)

    # Insert sample users if table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        sample_users = [
            (1, "alice"),
            (2, "bob")
        ]
        cursor.executemany('''
            INSERT INTO users (id, username)
            VALUES (?, ?)
        ''', sample_users)

    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.before_first_request
def initialize():
    # If running for the first time, initialize the DB.
    init_db()

@app.route("/product/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Retrieve product information by product ID."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    # Convert row to dict
    product_data = dict(product)
    return jsonify(product_data)

@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    """
    Add a product to a user's cart if the product has available stock.
    Expects JSON with keys: user_id, product_id, and optionally quantity (default is 1).
    """
    data = request.get_json()

    # Validate input
    if not data or "user_id" not in data or "product_id" not in data:
        return jsonify({"error": "user_id and product_id are required"}), 400

    user_id = data["user_id"]
    product_id = data["product_id"]
    quantity = data.get("quantity", 1)

    # Check if the user exists
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Retrieve the product
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # Check if the product has enough stock
    if product["stock"] < quantity:
        return jsonify({"error": "Insufficient stock"}), 400

    try:
        # Try to insert a new row for this user and product combination.
        cursor.execute('''
            INSERT INTO carts (user_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', (user_id, product_id, quantity))
    except sqlite3.IntegrityError:
        # If the product is already in the user's cart, update the quantity.
        cursor.execute('''
            UPDATE carts
            SET quantity = quantity + ?
            WHERE user_id = ? AND product_id = ?
        ''', (quantity, user_id, product_id))
    # Optionally, reduce the available stock if desired:
    # cursor.execute('''
    #     UPDATE products
    #     SET stock = stock - ?
    #     WHERE id = ?
    # ''', (quantity, product_id))

    db.commit()

    return jsonify({"message": "Product added to cart successfully"}), 200

# For testing purposes, we can add a route to display a user's cart.
@app.route("/cart/<int:user_id>", methods=["GET"])
def get_cart(user_id):
    """Retrieve all items in a user's cart."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT c.user_id, c.product_id, c.quantity, p.name, p.price
        FROM carts c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (user_id,))
    items = cursor.fetchall()
    cart_items = [dict(item) for item in items]
    return jsonify(cart_items)

if __name__ == '__main__':
    # Remove existing DB for a clean test environment (optional)
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    # Initialize DB before starting the app
    with app.app_context():
        init_db()
    # Run the Flask development server
    app.run(debug=True)
