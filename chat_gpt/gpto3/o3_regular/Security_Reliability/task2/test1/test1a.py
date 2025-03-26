from flask import Flask, request, jsonify, g
import sqlite3
import os

DATABASE = "ecommerce.db"
app = Flask(__name__)

# --- Database Utility Functions ---

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Use a file-based DB for persistence; change to ':memory:' if you prefer in-memory.
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows

def init_db():
    """Initializes the database with tables and some sample data."""
    db = get_db()
    with app.app_context():
        # Create tables if they do not exist.
        db.executescript("""
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS carts;
        
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            UNIQUE(user_id, product_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        """)
        db.commit()

        # Insert sample data if tables are empty
        if not query_db("SELECT id FROM users LIMIT 1", one=True):
            db.execute("INSERT INTO users (username) VALUES (?)", ("alice",))
            db.execute("INSERT INTO users (username) VALUES (?)", ("bob",))
        
        if not query_db("SELECT id FROM products LIMIT 1", one=True):
            db.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       ("Widget", "A useful widget", 9.99, 10))
            db.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       ("Gadget", "A fancy gadget", 19.99, 5))
        
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- API Endpoints ---

@app.route("/product/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Retrieve product information by product ID."""
    product = query_db("SELECT * FROM products WHERE id = ?", (product_id,), one=True)
    if product:
        return jsonify({key: product[key] for key in product.keys()}), 200
    else:
        return jsonify({"error": "Product not found"}), 404

@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    """
    Add a product to the user's cart.
    Expects JSON payload with:
      - user_id
      - product_id
      - quantity (optional, defaults to 1)
    Only adds the product if it's in stock (i.e. stock >= requested quantity).
    """
    data = request.get_json()
    if not data or "user_id" not in data or "product_id" not in data:
        return jsonify({"error": "Missing required fields: user_id and product_id"}), 400

    user_id = data["user_id"]
    product_id = data["product_id"]
    quantity = int(data.get("quantity", 1))
    
    db = get_db()

    # Check if product exists and if sufficient stock is available
    product = query_db("SELECT * FROM products WHERE id = ?", (product_id,), one=True)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    if product["stock"] < quantity:
        return jsonify({"error": "Insufficient stock"}), 400

    try:
        # Insert or update cart item using a transaction
        cursor = db.cursor()
        # Check if item is already in cart
        existing = query_db("SELECT * FROM carts WHERE user_id = ? AND product_id = ?",
                            (user_id, product_id), one=True)
        if existing:
            new_quantity = existing["quantity"] + quantity
            # Check if the new quantity exceeds available stock
            if product["stock"] < new_quantity:
                return jsonify({"error": "Insufficient stock for additional quantity"}), 400
            cursor.execute("UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?",
                           (new_quantity, user_id, product_id))
        else:
            cursor.execute("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
                           (user_id, product_id, quantity))
        
        # Update product stock accordingly
        cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                       (quantity, product_id))
        db.commit()
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500

    return jsonify({"message": "Product added to cart successfully"}), 200

@app.route("/cart/<int:user_id>", methods=["GET"])
def get_cart(user_id):
    """Retrieve all cart items for a given user."""
    items = query_db("""
        SELECT c.product_id, p.name, p.description, p.price, c.quantity 
        FROM carts c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    """, (user_id,))
    cart_items = [dict(item) for item in items]
    return jsonify(cart_items), 200

# --- Testing Functionality ---

def run_tests():
    """
    Run basic tests on the API endpoints using Flask's test client.
    """
    with app.test_client() as client:
        print("Testing GET /product/1 ...")
        response = client.get("/product/1")
        print("Response:", response.get_json())

        print("\nTesting POST /cart/add (adding 2 Widgets for user_id=1)...")
        response = client.post("/cart/add", json={"user_id": 1, "product_id": 1, "quantity": 2})
        print("Response:", response.get_json())

        print("\nTesting GET /cart/1 ...")
        response = client.get("/cart/1")
        print("Response:", response.get_json())

        print("\nTesting POST /cart/add (attempting to add more than in stock)...")
        # Assuming product 2 (Gadget) only has 5 in stock, try to add 6.
        response = client.post("/cart/add", json={"user_id": 1, "product_id": 2, "quantity": 6})
        print("Response:", response.get_json())

if __name__ == "__main__":
    # If the database file does not exist, initialize it.
    if not os.path.exists(DATABASE):
        with app.app_context():
            init_db()
            print("Database initialized with sample data.")

    # Uncomment the line below to run the tests from the command line.
    run_tests()

    # Start the Flask development server.
    app.run(debug=True)
