import sqlite3
from flask import Flask, request, jsonify, g

DATABASE = 'ecommerce.db'
app = Flask(__name__)

# ---------------------------
# Database Utility Functions
# ---------------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS carts")

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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            UNIQUE(user_id, product_id)
        )
    ''')

    # Insert sample data into products table if empty
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        sample_products = [
            (1, "Laptop", "High performance laptop", 1200.00, 5),
            (2, "Smartphone", "Latest model smartphone", 800.00, 10),
            (3, "Headphones", "Noise-cancelling headphones", 150.00, 0)  # out of stock
        ]
        cursor.executemany('INSERT INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)', sample_products)

    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ---------------------------
# API Endpoints
# ---------------------------

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    if product:
        return jsonify({key: product[key] for key in product.keys()}), 200
    else:
        return jsonify({"error": "Product not found"}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    # User identification via header
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({"error": "User identification missing in header (X-User-ID)"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user id"}), 400

    data = request.get_json()
    if not data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({"error": "Request JSON must include 'product_id' and 'quantity'"}), 400

    product_id = data['product_id']
    quantity = data['quantity']

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    db = get_db()
    cursor = db.cursor()

    # Check if product exists and has enough stock
    cursor.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({"error": "Product not found"}), 404

    available_stock = row['stock']
    if available_stock < quantity:
        return jsonify({"error": f"Not enough stock available. Available: {available_stock}"}), 400

    # Add to cart
    try:
        # Here, we use an UPSERT pattern so that if the product is already in the cart, we update the quantity
        cursor.execute('''
            INSERT INTO carts (user_id, product_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id)
            DO UPDATE SET quantity = carts.quantity + ?
        ''', (user_id, product_id, quantity, quantity))
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

    # Optionally, reduce product stock after adding to cart
    cursor.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (quantity, product_id))
    db.commit()

    return jsonify({"message": f"Added {quantity} of product {product_id} to user {user_id}'s cart."}), 200

# ---------------------------
# Test Endpoint
# ---------------------------
@app.route('/')
def index():
    return jsonify({
        "message": "Welcome to the E-commerce API. Use /product/<product_id> to retrieve product info and /cart/add to add a product to your cart."
    })

# ---------------------------
# Main Execution
# ---------------------------
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
