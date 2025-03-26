from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # enables name-based access to columns
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Create users table
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
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # Create cart_items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY,
            cart_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (cart_id) REFERENCES carts(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    conn.commit()
    conn.close()

def seed_data():
    conn = get_db()
    cursor = conn.cursor()
    # Seed users if none exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username) VALUES (?)", ("alice",))
        cursor.execute("INSERT INTO users (username) VALUES (?)", ("bob",))
    # Seed products if none exist
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       ("Laptop", "High performance laptop", 999.99, 10))
        cursor.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       ("Headphones", "Noise cancelling headphones", 199.99, 5))
        # This product is out of stock
        cursor.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       ("Smartphone", "Latest model smartphone", 799.99, 0))
    conn.commit()
    conn.close()

@app.route('/api/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    # Secure parameterized query prevents SQL injection
    cursor.execute("SELECT id, name, description, price, stock FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if product:
        return jsonify(dict(product)), 200
    else:
        return jsonify({"error": "Product not found"}), 404

def get_or_create_cart(user_id, cursor):
    # Retrieve the cart for the user or create one if it doesn't exist
    cursor.execute("SELECT id FROM carts WHERE user_id = ?", (user_id,))
    cart = cursor.fetchone()
    if cart:
        return cart[0]
    else:
        cursor.execute("INSERT INTO carts (user_id) VALUES (?)", (user_id,))
        return cursor.lastrowid

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    user_id = data.get("user_id")
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not all([user_id, product_id]):
        return jsonify({"error": "Missing user_id or product_id"}), 400

    try:
        quantity = int(quantity)
        if quantity < 1:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Validate user exists
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    # Validate product exists and check available stock
    cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        conn.close()
        return jsonify({"error": "Product not found"}), 404

    available_stock = product["stock"]
    if available_stock < quantity:
        conn.close()
        return jsonify({"error": "Insufficient stock available"}), 400

    # Retrieve or create the user's cart
    cart_id = get_or_create_cart(user_id, cursor)

    # If the product is already in the cart, update the quantity
    cursor.execute("SELECT id, quantity FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, product_id))
    existing_item = cursor.fetchone()
    if existing_item:
        new_quantity = existing_item["quantity"] + quantity
        if new_quantity > available_stock:
            conn.close()
            return jsonify({"error": "Adding this quantity exceeds available stock"}), 400
        cursor.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_quantity, existing_item["id"]))
    else:
        cursor.execute("INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (?, ?, ?)",
                       (cart_id, product_id, quantity))

    conn.commit()
    conn.close()
    return jsonify({"message": "Product added to cart successfully"}), 200

# Additional endpoint for testing: view the cart items for a user
@app.route('/api/cart/<int:user_id>', methods=['GET'])
def view_cart(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM carts WHERE user_id = ?", (user_id,))
    cart = cursor.fetchone()
    if not cart:
        conn.close()
        return jsonify({"message": "Cart is empty"}), 200

    cart_id = cart["id"]
    cursor.execute("""
        SELECT p.id as product_id, p.name, p.description, p.price, ci.quantity
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.cart_id = ?
    """, (cart_id,))
    items = cursor.fetchall()
    conn.close()
    return jsonify({"cart_items": [dict(item) for item in items]}), 200

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
        seed_data()
    app.run(debug=True)
