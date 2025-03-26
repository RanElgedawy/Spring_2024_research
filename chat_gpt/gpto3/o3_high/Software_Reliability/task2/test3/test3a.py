from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS cart_items")

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL
        )
    ''')
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            stock INTEGER DEFAULT 0
        )
    ''')
    # Create cart_items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    db.commit()

def seed_db():
    db = get_db()
    cursor = db.cursor()
    # Seed sample users (if they don't already exist)
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (1, "Alice"))
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (2, "Bob"))
    # Seed sample products
    cursor.execute(
        "INSERT OR IGNORE INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)",
        (1, "Widget", "A useful widget", 9.99, 10)
    )
    cursor.execute(
        "INSERT OR IGNORE INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)",
        (2, "Gadget", "A fancy gadget", 19.99, 0)  # Out of stock
    )
    db.commit()

@app.before_first_request
def setup():
    init_db()
    seed_db()

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if product:
        return jsonify({
            "id": product["id"],
            "name": product["name"],
            "description": product["description"],
            "price": product["price"],
            "stock": product["stock"]
        })
    return jsonify({"error": "Product not found"}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    if not data or 'product_id' not in data:
        return jsonify({"error": "Product ID required"}), 400

    product_id = data['product_id']
    quantity = data.get('quantity', 1)
    
    # Assume user identification is provided in the header
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({"error": "User identification required in X-User-ID header"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user id"}), 400

    db = get_db()
    cursor = db.cursor()
    # Retrieve product and verify stock availability
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({"error": "Product not found"}), 404

    if product["stock"] < quantity:
        return jsonify({"error": "Not enough stock available"}), 400

    # Update the product stock
    new_stock = product["stock"] - quantity
    cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))

    # Add to cart: check if item already exists in the user's cart
    cursor.execute("SELECT * FROM cart_items WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    cart_item = cursor.fetchone()
    if cart_item:
        new_quantity = cart_item["quantity"] + quantity
        cursor.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_quantity, cart_item["id"]))
    else:
        cursor.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                       (user_id, product_id, quantity))
    db.commit()
    return jsonify({"message": "Product added to cart"}), 200

# Endpoint to view the cart for a given user
@app.route('/cart', methods=['GET'])
def view_cart():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({"error": "User identification required in X-User-ID header"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user id"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT c.id as cart_item_id, c.quantity, p.id as product_id, p.name, p.price
        FROM cart_items c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    """, (user_id,))
    items = cursor.fetchall()
    cart = [{
        "cart_item_id": item["cart_item_id"],
        "product_id": item["product_id"],
        "name": item["name"],
        "price": item["price"],
        "quantity": item["quantity"]
    } for item in items]
    return jsonify({"cart": cart})

if __name__ == '__main__':
    app.run(debug=True)
