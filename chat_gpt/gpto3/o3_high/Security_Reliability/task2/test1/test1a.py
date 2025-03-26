from flask import Flask, request, jsonify, abort
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # so we can return dict-like rows
    return conn

def init_db():
    """Creates tables if they don't exist and adds sample data for testing."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS users")
    
    # Create products table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')

    # Create users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL
        )
    ''')

    # Create carts table with a UNIQUE constraint for (user_id, product_id)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            UNIQUE(user_id, product_id)
        )
    ''')

    # Insert sample products if they don't exist
    products = [
        (1, 'Laptop', 'High performance laptop', 1000.0, 5),
        (2, 'Headphones', 'Noise cancelling headphones', 200.0, 10),
        (3, 'Mouse', 'Wireless mouse', 50.0, 0)  # out-of-stock product for testing
    ]
    for p in products:
        cur.execute('''
            INSERT OR IGNORE INTO products (id, name, description, price, stock)
            VALUES (?, ?, ?, ?, ?)
        ''', p)

    # Insert sample users if they don't exist
    users = [
        (1, 'alice'),
        (2, 'bob')
    ]
    for u in users:
        cur.execute('''
            INSERT OR IGNORE INTO users (id, username)
            VALUES (?, ?)
        ''', u)

    conn.commit()
    conn.close()

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Retrieve product information by product ID."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cur.fetchone()
    conn.close()
    if product is None:
        abort(404, description="Product not found")
    return jsonify(dict(product))

@app.route('/cart', methods=['POST'])
def add_to_cart():
    """
    Add a product to a user's cart.
    Expects JSON with:
      - user_id: int
      - product_id: int
      - quantity: int (optional, default is 1)
    Only allows addition if the product exists and is in stock.
    """
    data = request.get_json()
    if not data or 'user_id' not in data or 'product_id' not in data:
        abort(400, description="Missing required parameters")

    user_id = data['user_id']
    product_id = data['product_id']
    quantity = data.get('quantity', 1)
    if quantity < 1:
        abort(400, description="Quantity must be at least 1")

    conn = get_db_connection()
    cur = conn.cursor()

    # Check if user exists
    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    if user is None:
        conn.close()
        abort(400, description="User does not exist")

    # Check if product exists and is in stock (stock must be >= requested quantity)
    cur.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cur.fetchone()
    if product is None:
        conn.close()
        abort(400, description="Product does not exist")
    if product['stock'] < quantity:
        conn.close()
        abort(400, description="Not enough stock available")

    # Check if the product is already in the user's cart; if so, update quantity.
    cur.execute('SELECT * FROM carts WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    cart_item = cur.fetchone()
    if cart_item:
        new_quantity = cart_item['quantity'] + quantity
        cur.execute('''
            UPDATE carts
            SET quantity = ?
            WHERE user_id = ? AND product_id = ?
        ''', (new_quantity, user_id, product_id))
    else:
        cur.execute('''
            INSERT INTO carts (user_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', (user_id, product_id, quantity))

    conn.commit()
    conn.close()
    return jsonify({"message": "Item added to cart"}), 201

@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    """Retrieve all items in a user's cart along with product details."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Verify user exists
    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    if user is None:
        conn.close()
        abort(400, description="User does not exist")

    # Retrieve cart items with join to get product details
    cur.execute('''
        SELECT c.quantity, p.id AS product_id, p.name, p.description, p.price
        FROM carts c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (user_id,))
    items = cur.fetchall()
    conn.close()

    cart = [dict(item) for item in items]
    return jsonify({"user_id": user_id, "cart": cart})

if __name__ == '__main__':
    # Initialize the database (creates tables and sample data if they don't exist)
    if not os.path.exists(DATABASE):
        init_db()
    else:
        # Even if the DB file exists, you might want to ensure the schema is in place
        init_db()
    app.run(debug=True)
