import sqlite3
from flask import Flask, request, jsonify, g
from datetime import datetime

DATABASE = 'ecommerce.db'

app = Flask(__name__)

# --- Database Helpers ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Connect using SQLite. Using detect_types for dates if needed.
        db = g._database = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def init_db():
    """Creates the tables and inserts sample data if they do not exist."""
    db = get_db()
    db.execute("DROP TABLE IF EXISTS product")
    db.execute("DROP TABLE IF EXISTS user")
    db.execute("DROP TABLE IF EXISTS cart")

    # Create product table (simulate pre-existing product DB)
    db.execute('''
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        );
    ''')
    # Create user table (simulate pre-existing user DB)
    db.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE
        );
    ''')
    # Create cart table (for storing user cart items)
    db.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            added_at TIMESTAMP NOT NULL,
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(product_id) REFERENCES product(id)
        );
    ''')
    db.commit()

    # Insert sample data into product table if empty
    products = query_db('SELECT * FROM product')
    if not products:
        sample_products = [
            (1, 'Widget A', 19.99, 10),
            (2, 'Widget B', 29.99, 5),
            (3, 'Widget C', 9.99, 0)  # Out of stock example
        ]
        db.executemany('INSERT INTO product (id, name, price, stock) VALUES (?, ?, ?, ?);', sample_products)
        db.commit()

    # Insert sample data into user table if empty
    users = query_db('SELECT * FROM user')
    if not users:
        sample_users = [
            (1, 'alice'),
            (2, 'bob')
        ]
        db.executemany('INSERT INTO user (id, username) VALUES (?, ?);', sample_users)
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- API Endpoints ---
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Retrieve product information by product ID."""
    product = query_db('SELECT * FROM product WHERE id = ?;', [product_id], one=True)
    if product is None:
        return jsonify({'error': 'Product not found'}), 404

    product_data = {
        'id': product['id'],
        'name': product['name'],
        'price': product['price'],
        'stock': product['stock']
    }
    return jsonify(product_data)

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """
    Add a product to a user's cart.
    Expected JSON payload: {
        "user_id": <int>,
        "product_id": <int>,
        "quantity": <int>
    }
    Only adds product if enough stock is available.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    # Validate required fields
    for field in ('user_id', 'product_id', 'quantity'):
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    try:
        user_id = int(data['user_id'])
        product_id = int(data['product_id'])
        quantity = int(data['quantity'])
    except ValueError:
        return jsonify({'error': 'user_id, product_id, and quantity must be integers'}), 400

    if quantity < 1:
        return jsonify({'error': 'Quantity must be at least 1'}), 400

    db = get_db()
    # Check if the user exists
    user = query_db('SELECT * FROM user WHERE id = ?;', [user_id], one=True)
    if user is None:
        return jsonify({'error': 'User not found'}), 404

    # Check product availability
    product = query_db('SELECT * FROM product WHERE id = ?;', [product_id], one=True)
    if product is None:
        return jsonify({'error': 'Product not found'}), 404

    if product['stock'] < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400

    # Securely add to cart using parameterized query
    cur = db.execute('''
        INSERT INTO cart (user_id, product_id, quantity, added_at)
        VALUES (?, ?, ?, ?);
    ''', (user_id, product_id, quantity, datetime.utcnow()))
    # Optionally update product stock to simulate reserving items
    new_stock = product['stock'] - quantity
    db.execute('UPDATE product SET stock = ? WHERE id = ?;', (new_stock, product_id))
    db.commit()

    return jsonify({
        'message': 'Product added to cart successfully',
        'cart_item_id': cur.lastrowid,
        'remaining_stock': new_stock
    }), 201

# --- Testing Helper ---
@app.route('/cart', methods=['GET'])
def get_cart():
    """Retrieve all items in the cart (for testing purposes)."""
    cart_items = query_db('SELECT * FROM cart;')
    results = []
    for item in cart_items:
        results.append({
            'id': item['id'],
            'user_id': item['user_id'],
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'added_at': item['added_at']
        })
    return jsonify(results)

# --- Main Entry Point ---
if __name__ == '__main__':
    with app.app_context():
        init_db()
    # Run the Flask development server
    app.run(debug=True)
