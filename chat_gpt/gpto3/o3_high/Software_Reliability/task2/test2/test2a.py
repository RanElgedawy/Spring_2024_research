import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DATABASE = "ecommerce.db"

def get_db():
    """Helper to connect to the SQLite DB and return rows as dictionaries."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Automatically creates tables if they do not exist."""
    conn = get_db()
    c = conn.cursor()
    # Create a users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL
        )
    ''')
    # Create a products table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    # Create a cart_items table that associates a user with product items and quantity
    c.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    conn.commit()
    conn.close()

def populate_test_data():
    """Insert some test data if tables are empty."""
    conn = get_db()
    c = conn.cursor()
    # Insert a test user if none exist
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username) VALUES (?)", ("testuser",))
    # Insert some test products if none exist
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        products = [
            ("Laptop", "A powerful laptop", 999.99, 10),
            ("Smartphone", "A feature-rich smartphone", 599.99, 5),
            ("Headphones", "Noise-cancelling headphones", 199.99, 0)  # Out of stock
        ]
        c.executemany("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)", products)
    conn.commit()
    conn.close()

@app.route('/api/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Retrieve product information by product ID.
    Example:
      GET /api/product/1
    """
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(dict(product))

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """
    Add a product to the user's cart if it has available stock.
    The user must be identified via the "X-User-ID" header.
    The JSON body should include "product_id" and an optional "quantity" (default is 1).
    
    Example using curl:
      curl -H "Content-Type: application/json" \
           -H "X-User-ID: 1" \
           -X POST -d '{"product_id": 1, "quantity": 2}' \
           http://127.0.0.1:5000/api/cart/add
    """
    # Get the user ID from header
    user_id = request.headers.get('X-User-ID')
    if user_id is None:
        return jsonify({"error": "User ID not provided"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid User ID"}), 400

    data = request.get_json()
    if not data or 'product_id' not in data:
        return jsonify({"error": "Product ID is required"}), 400
    product_id = data['product_id']
    quantity = data.get('quantity', 1)
    try:
        quantity = int(quantity)
    except ValueError:
        return jsonify({"error": "Invalid quantity"}), 400
    if quantity <= 0:
        return jsonify({"error": "Quantity must be positive"}), 400

    conn = get_db()
    c = conn.cursor()
    
    # Check if the user exists
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    if c.fetchone() is None:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    # Check if the product exists and if there is sufficient stock
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    if product is None:
        conn.close()
        return jsonify({"error": "Product not found"}), 404
    if product['stock'] < quantity:
        conn.close()
        return jsonify({"error": "Insufficient stock"}), 400

    # Check if the product is already in the user's cart
    c.execute("SELECT * FROM cart_items WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    cart_item = c.fetchone()
    if cart_item:
        # Update the quantity if the product is already in the cart
        new_quantity = cart_item['quantity'] + quantity
        if product['stock'] < new_quantity:
            conn.close()
            return jsonify({"error": "Insufficient stock for additional quantity"}), 400
        c.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_quantity, cart_item['id']))
    else:
        # Insert a new cart item
        c.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                  (user_id, product_id, quantity))
    
    # Optionally update product stock to reserve the item
    c.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Product added to cart successfully"})

@app.route('/api/cart', methods=['GET'])
def get_cart():
    """
    For testing purposes: Retrieve the cart items for the authenticated user.
    The user must be identified via the "X-User-ID" header.
    
    Example using curl:
      curl -H "X-User-ID: 1" http://127.0.0.1:5000/api/cart
    """
    user_id = request.headers.get('X-User-ID')
    if user_id is None:
        return jsonify({"error": "User ID not provided"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid User ID"}), 400

    conn = get_db()
    c = conn.cursor()
    # Join cart items with product details for easier testing
    c.execute("""
        SELECT cart_items.*, products.name, products.price
        FROM cart_items
        JOIN products ON cart_items.product_id = products.id
        WHERE cart_items.user_id = ?
    """, (user_id,))
    items = c.fetchall()
    conn.close()
    return jsonify([dict(item) for item in items])

if __name__ == '__main__':
    # Initialize the database and pre-populate test data
    init_db()
    populate_test_data()
    
    # Print testing instructions to the console
    print("Testing instructions:")
    print("1. Retrieve product details:")
    print("   curl http://127.0.0.1:5000/api/product/1")
    print("2. Add a product to the cart (requires X-User-ID header):")
    print("   curl -H \"Content-Type: application/json\" -H \"X-User-ID: 1\" -X POST -d '{\"product_id\": 1, \"quantity\": 1}' http://127.0.0.1:5000/api/cart/add")
    print("3. Check the cart contents:")
    print("   curl -H \"X-User-ID: 1\" http://127.0.0.1:5000/api/cart")
    
    # Start the Flask development server
    app.run(debug=True)
