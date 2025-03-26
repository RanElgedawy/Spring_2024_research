from flask import Flask, request, jsonify, g
import sqlite3
import os

app = Flask(__name__)
DATABASE = "ecommerce.db"

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        # connect to the SQLite DB; if it doesn't exist, it will be created automatically
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # enable name-based access to columns
    return db

def init_db():
    """Initialize the database with the necessary tables and sample data."""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS products")

    # Create users table (for demonstration)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    
    # Create carts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Insert sample users (if not already present)
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (1, "alice"))
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (2, "bob"))
    
    # Insert sample products (if not already present)
    sample_products = [
        (1, "T-Shirt", "A comfortable cotton T-shirt", 19.99, 10),
        (2, "Coffee Mug", "Ceramic mug with logo", 9.99, 0),  # Out of stock example
        (3, "Sneakers", "Running sneakers", 49.99, 5)
    ]
    for prod in sample_products:
        cursor.execute('''
            INSERT OR IGNORE INTO products (id, name, description, price, stock)
            VALUES (?, ?, ?, ?, ?)
        ''', prod)
    
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/product/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """
    Retrieve product information by product_id.
    Returns 404 if product is not found.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    product_data = {
        "id": product["id"],
        "name": product["name"],
        "description": product["description"],
        "price": product["price"],
        "stock": product["stock"]
    }
    return jsonify(product_data)

@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    """
    Add a product to the user's cart.
    
    Expects JSON payload:
    {
      "product_id": <int>,
      "quantity": <int> (optional, default=1)
    }
    
    The user ID is taken from the X-User-ID header.
    Checks that the product exists and has enough stock.
    """
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"error": "Missing X-User-ID header"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid X-User-ID header"}), 400

    data = request.get_json()
    if not data or "product_id" not in data:
        return jsonify({"error": "Missing product_id in JSON body"}), 400

    product_id = data["product_id"]
    quantity = data.get("quantity", 1)
    if quantity < 1:
        return jsonify({"error": "Quantity must be at least 1"}), 400

    db = get_db()
    cursor = db.cursor()

    # Check if product exists and has enough stock
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    if product["stock"] < quantity:
        return jsonify({"error": "Not enough stock available"}), 400

    # Add product to cart
    # For simplicity, we insert a new row. In a real-world app you might want to combine rows if product already exists in the cart.
    cursor.execute('''
        INSERT INTO carts (user_id, product_id, quantity)
        VALUES (?, ?, ?)
    ''', (user_id, product_id, quantity))

    # Optionally, update product stock (simulate reserving the items)
    cursor.execute('''
        UPDATE products SET stock = stock - ? WHERE id = ?
    ''', (quantity, product_id))

    db.commit()

    return jsonify({"message": f"Added product {product_id} (quantity: {quantity}) to user {user_id}'s cart."})

if __name__ == "__main__":
    # If running for the first time, initialize the DB (creates tables and sample data)
    if not os.path.exists(DATABASE):
        with app.app_context():
            init_db()
            print("Initialized database with sample data.")
    else:
        # Optionally, you could run init_db() on each start if you want to ensure tables exist.
        with app.app_context():
            init_db()

    # Start the Flask development server
    app.run(debug=True)
