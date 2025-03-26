from flask import Flask, request, jsonify
import sqlite3
import os

DATABASE = "ecommerce.db"

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    # Return rows as dictionaries for convenience
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # If the database does not exist, create tables and insert sample data.
    db_exists = os.path.exists(DATABASE)
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS carts")

    # Create products table (simulate that it exists)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    # Create users table (simulate that it exists)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE
        )
    """)

    # Create carts table to store user cart items.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)

    # If the DB is new, insert some sample products and users.
    # if not db_exists:
    # Sample products
    sample_products = [
        (1, "Widget", "A useful widget", 19.99, 10),
        (2, "Gadget", "A fancy gadget", 29.99, 5),
        (3, "Doohickey", "An amazing doohickey", 9.99, 0)  # Out of stock sample
    ]
    cur.executemany("INSERT OR IGNORE INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)", sample_products)

    # Sample users
    sample_users = [
        (1, "alice"),
        (2, "bob")
    ]
    cur.executemany("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", sample_users)

    conn.commit()
    conn.close()

@app.route('/')
def index():
    instructions = {
        "message": "Welcome to the e-commerce API.",
        "endpoints": {
            "GET /product/<product_id>": "Retrieve product information by product ID.",
            "POST /cart/add": {
                "description": "Add a product to a user's cart. Only in-stock products are allowed.",
                "payload": {
                    "user_id": "ID of the user",
                    "product_id": "ID of the product",
                    "quantity": "Quantity to add (must be <= available stock)"
                }
            }
        },
        "test_instructions": "Use a REST client (like curl or Postman) to test these endpoints. For example, to add a product: POST JSON {\"user_id\": 1, \"product_id\": 1, \"quantity\": 2} to /cart/add."
    }
    return jsonify(instructions)

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    # Parameterized query to avoid SQL injection.
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()
    conn.close()

    if product:
        return jsonify(dict(product))
    else:
        return jsonify({"error": "Product not found"}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()

    if not data or not all(k in data for k in ("user_id", "product_id", "quantity")):
        return jsonify({"error": "Missing required fields: user_id, product_id, and quantity"}), 400

    user_id = data["user_id"]
    product_id = data["product_id"]
    quantity = data["quantity"]

    # Validate quantity is a positive integer
    if not isinstance(quantity, int) or quantity < 1:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Check that user exists
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    # Check that product exists and is in stock
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()
    if not product:
        conn.close()
        return jsonify({"error": "Product not found"}), 404

    available_stock = product["stock"]
    if available_stock < quantity:
        conn.close()
        return jsonify({"error": "Not enough stock available", "available_stock": available_stock}), 400

    # Add the product to the cart
    cur.execute("""
        INSERT INTO carts (user_id, product_id, quantity)
        VALUES (?, ?, ?)
    """, (user_id, product_id, quantity))

    # Optionally update the products table to reflect reduced stock.
    cur.execute("""
        UPDATE products
        SET stock = stock - ?
        WHERE id = ?
    """, (quantity, product_id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Product added to cart successfully"})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
