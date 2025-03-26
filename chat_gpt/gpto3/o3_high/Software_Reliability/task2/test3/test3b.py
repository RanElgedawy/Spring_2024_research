from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Create a table for users
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("DROP TABLE IF EXISTS cart")

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT
        )
    ''')
    # Create a table for products
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL,
            stock INTEGER
        )
    ''')
    # Create a table for cart items
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            UNIQUE(user_id, product_id)
        )
    ''')
    conn.commit()
    
    # Insert sample users if table is empty
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users (username) VALUES (?)", ("alice",))
        cur.execute("INSERT INTO users (username) VALUES (?)", ("bob",))
        conn.commit()
    
    # Insert sample products if table is empty
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", ("Widget", 9.99, 10))
        cur.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", ("Gadget", 14.99, 0))
        conn.commit()
    conn.close()

@app.route('/api/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Retrieve product information by product ID."""
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    # Return product information as JSON
    return jsonify(dict(product))

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """
    Add a product to a user's cart.
    Expects the following:
      - HTTP header "X-User-ID" for user identification.
      - JSON payload with "product_id" and "quantity".
    """
    # Ensure the user is identified
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'User ID is required in X-User-ID header'}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid User ID'}), 400

    # Get JSON payload
    data = request.get_json()
    if not data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Request must contain product_id and quantity'}), 400

    product_id = data['product_id']
    quantity = data['quantity']
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    
    # Optionally verify user exists
    user = cur.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    # Check product existence and stock
    product = cur.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404
    if product['stock'] < quantity:
        conn.close()
        return jsonify({'error': 'Insufficient stock available'}), 400

    # Add product to cart or update existing entry if it already exists
    existing_cart = cur.execute("SELECT * FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id)).fetchone()
    if existing_cart:
        new_quantity = existing_cart['quantity'] + quantity
        cur.execute("UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?",
                    (new_quantity, user_id, product_id))
    else:
        cur.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
                    (user_id, product_id, quantity))

    # Optionally update the product stock to reflect items reserved in the cart
    new_stock = product['stock'] - quantity
    cur.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Product added to cart successfully'})

@app.route('/api/cart', methods=['GET'])
def get_cart():
    """
    Retrieve the current user's cart.
    Requires HTTP header "X-User-ID".
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'User ID is required in X-User-ID header'}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid User ID'}), 400

    conn = get_db_connection()
    # Join cart and products to return useful product info along with quantity.
    cart_items = conn.execute('''
        SELECT cart.product_id, products.name, products.price, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()

    items = [dict(item) for item in cart_items]
    return jsonify({'cart': items})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
