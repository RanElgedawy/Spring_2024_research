from flask import Flask, request, jsonify, g
import sqlite3

DATABASE = 'ecommerce.db'
app = Flask(__name__)

# Get or create a DB connection per request
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Using sqlite3 with row_factory to return dictionaries for easy JSON conversion
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

# Close the DB connection when the app context ends
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize the DB tables if they don't exist
def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS cart_items")
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                       id INTEGER PRIMARY KEY,
                       name TEXT NOT NULL,
                       description TEXT,
                       price REAL,
                       stock INTEGER NOT NULL
                       )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                       id INTEGER PRIMARY KEY,
                       username TEXT NOT NULL UNIQUE
                       )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cart_items (
                       id INTEGER PRIMARY KEY,
                       user_id INTEGER,
                       product_id INTEGER,
                       quantity INTEGER NOT NULL,
                       FOREIGN KEY(user_id) REFERENCES users(id),
                       FOREIGN KEY(product_id) REFERENCES products(id)
                       )''')
    db.commit()

# Populate the DB with some sample data for testing.
def populate_sample_data():
    db = get_db()
    cursor = db.cursor()
    # Insert sample products if none exist
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        products = [
            (1, "Laptop", "High-performance gaming laptop", 1200.00, 5),
            (2, "Headphones", "Noise-cancelling headphones", 200.00, 10),
            (3, "Keyboard", "Mechanical keyboard", 150.00, 0)  # out of stock
        ]
        cursor.executemany(
            "INSERT INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)",
            products
        )
    # Insert a sample user if none exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        users = [
            (1, "testuser")
        ]
        cursor.executemany(
            "INSERT INTO users (id, username) VALUES (?, ?)",
            users
        )
    db.commit()

# API to retrieve product information by product ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    cursor = db.cursor()
    # Parameterized query to avoid SQL injection
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if product:
        return jsonify(dict(product)), 200
    else:
        return jsonify({"error": "Product not found"}), 404

# API to add a product to a user's cart (only if enough stock exists)
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    user_id = data.get("user_id")
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    if not user_id or not product_id:
        return jsonify({"error": "user_id and product_id are required"}), 400

    db = get_db()
    cursor = db.cursor()
    
    # Ensure the user exists
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Ensure the product exists and has sufficient stock
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({"error": "Product not found"}), 404
    if product["stock"] < quantity:
        return jsonify({"error": "Not enough stock available"}), 400

    # If the product is already in the user's cart, update the quantity (ensuring stock limits)
    cursor.execute("SELECT * FROM cart_items WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    cart_item = cursor.fetchone()
    if cart_item:
        new_quantity = cart_item["quantity"] + quantity
        if new_quantity > product["stock"]:
            return jsonify({"error": "Not enough stock available for the requested quantity"}), 400
        cursor.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_quantity, cart_item["id"]))
    else:
        cursor.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                       (user_id, product_id, quantity))
    db.commit()
    return jsonify({"message": "Product added to cart"}), 200

# API to retrieve a user's cart details
@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    db = get_db()
    cursor = db.cursor()
    # Join cart items with product info for a richer response
    cursor.execute("""
        SELECT ci.id, ci.quantity, p.id as product_id, p.name, p.description, p.price
        FROM cart_items ci 
        JOIN products p ON ci.product_id = p.id 
        WHERE ci.user_id = ?
    """, (user_id,))
    cart_items = cursor.fetchall()
    cart_list = [dict(item) for item in cart_items]
    return jsonify(cart_list), 200

# A simple testing endpoint to simulate API calls
@app.route('/test', methods=['GET'])
def run_tests():
    test_results = {}
    with app.test_client() as client:
        # Test product retrieval
        response = client.get('/product/1')
        test_results["get_product"] = response.get_json()
        # Test adding a product that is in stock
        response = client.post('/cart/add', json={"user_id": 1, "product_id": 1, "quantity": 1})
        test_results["add_to_cart_success"] = response.get_json()
        # Test adding a product that is out of stock (product_id 3 has 0 stock)
        response = client.post('/cart/add', json={"user_id": 1, "product_id": 3, "quantity": 1})
        test_results["add_to_cart_out_of_stock"] = response.get_json()
        # Test retrieving the cart
        response = client.get('/cart/1')
        test_results["get_cart"] = response.get_json()
    return jsonify(test_results), 200

if __name__ == '__main__':
    with app.app_context():
        init_db()
        populate_sample_data()
    # Running in debug mode for testing; disable debug in production
    app.run(debug=True)
