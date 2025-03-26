from flask import Flask, request, jsonify, g
import sqlite3
import os

DATABASE = "ecommerce.db"
app = Flask(__name__)

# ----------------------------
# Database helper functions
# ----------------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Connect to the SQLite database (creates file if not exists)
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # enables name-based access
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ----------------------------
# Database initialization
# ----------------------------
def init_db():
    db = get_db()
    # Create tables if they don't exist.
    db.executescript("""
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS cart;
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL
    );
    
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        stock INTEGER NOT NULL CHECK(stock >= 0)
    );
    
    CREATE TABLE IF NOT EXISTS cart (
        cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    );
    """)
    db.commit()

    # Insert sample data if not present.
    # For users table.
    if not query_db("SELECT * FROM users WHERE user_id = ?", (1,), one=True):
        execute_db("INSERT INTO users (user_id, username) VALUES (?, ?)", (1, "testuser"))
    # For products table.
    if not query_db("SELECT * FROM products WHERE product_id = ?", (1,), one=True):
        execute_db("INSERT INTO products (product_id, name, stock) VALUES (?, ?, ?)", (1, "Test Product", 5))
    if not query_db("SELECT * FROM products WHERE product_id = ?", (2,), one=True):
        execute_db("INSERT INTO products (product_id, name, stock) VALUES (?, ?, ?)", (2, "Out of Stock Product", 0))

# ----------------------------
# API Endpoints
# ----------------------------
@app.route("/api/product/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Retrieve product information by product ID."""
    product = query_db("SELECT * FROM products WHERE product_id = ?", (product_id,), one=True)
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({
        "product_id": product["product_id"],
        "name": product["name"],
        "stock": product["stock"]
    })

@app.route("/api/cart", methods=["POST"])
def add_to_cart():
    """
    Add a product to the user's cart.
    Expected JSON input: {"user_id": <int>, "product_id": <int>}
    Only adds product if it exists and is in stock. If successful, it decrements the product stock.
    """
    data = request.get_json()
    if not data or "user_id" not in data or "product_id" not in data:
        return jsonify({"error": "Invalid input. Must provide 'user_id' and 'product_id'."}), 400

    user_id = data["user_id"]
    product_id = data["product_id"]

    # Verify user exists.
    user = query_db("SELECT * FROM users WHERE user_id = ?", (user_id,), one=True)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    # Verify product exists and is in stock.
    product = query_db("SELECT * FROM products WHERE product_id = ?", (product_id,), one=True)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    if product["stock"] < 1:
        return jsonify({"error": "Product is out of stock"}), 400

    # Securely add product to cart using parameterized queries.
    try:
        execute_db("INSERT INTO cart (user_id, product_id) VALUES (?, ?)", (user_id, product_id))
        # Optionally, decrement the stock (if you want to reserve the item).
        execute_db("UPDATE products SET stock = stock - 1 WHERE product_id = ?", (product_id,))
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500

    return jsonify({"message": "Product added to cart successfully."}), 200

# ----------------------------
# Testing Endpoint (Optional)
# ----------------------------
@app.route("/api/cart/test", methods=["GET"])
def get_cart_contents():
    """
    Retrieve all cart entries for testing purposes.
    """
    cart_items = query_db("SELECT * FROM cart")
    results = []
    for item in cart_items:
        results.append({"cart_id": item["cart_id"], "user_id": item["user_id"], "product_id": item["product_id"]})
    return jsonify(results)

# ----------------------------
# Main block
# ----------------------------
if __name__ == "__main__":
    # Remove existing DB for a clean start (optional, comment out in production)
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    with app.app_context():
        init_db()
    # Run the Flask development server
    app.run(debug=True)
