import sqlite3
from flask import Flask, request, jsonify, g
import os

DATABASE = 'ecommerce.db'

def get_db():
    """Get a database connection that lasts for the request."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return db

def init_db():
    """Initialize the database with necessary tables if they don't exist."""
    db = get_db()
    # For demonstration, create a products table
    db.execute("DROP TABLE IF EXISTS products")
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("DROP TABLE IF EXISTS carts")

    db.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    # For demonstration, create a users table
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL
        )
    ''')
    # Create a carts table to store cart items per user
    db.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    db.commit()

def populate_dummy_data():
    """Populate sample data for products and users if the tables are empty."""
    db = get_db()
    # Populate products table if empty
    cur = db.execute('SELECT COUNT(*) as count FROM products')
    if cur.fetchone()['count'] == 0:
        db.executemany(
            'INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)', 
            [
                ('Widget A', 'High quality widget', 9.99, 10),
                ('Widget B', 'Another great widget', 19.99, 5),
                ('Widget C', 'Premium widget', 29.99, 0)  # Out of stock example
            ]
        )
    # Populate users table if empty
    cur = db.execute('SELECT COUNT(*) as count FROM users')
    if cur.fetchone()['count'] == 0:
        db.executemany(
            'INSERT INTO users (username) VALUES (?)', 
            [
                ('alice',),
                ('bob',)
            ]
        )
    db.commit()

app = Flask(__name__)

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection at the end of each request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Retrieve product details by product ID."""
    db = get_db()
    cur = db.execute(
        'SELECT id, name, description, price, stock FROM products WHERE id = ?', 
        (product_id,)
    )
    product = cur.fetchone()
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(dict(product))

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """
    Add a product to a user's cart.
    Expected JSON payload:
      { "user_id": <int>, "product_id": <int>, "quantity": <int> }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400

    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id or not product_id:
        return jsonify({'error': 'user_id and product_id are required'}), 400

    db = get_db()
    # Check if the product exists and has enough stock
    cur = db.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
    product = cur.fetchone()
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    if product['stock'] < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Check if the user exists
    cur = db.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Insert cart item using a parameterized query to avoid SQL injection
    db.execute(
        'INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)', 
        (user_id, product_id, quantity)
    )
    db.commit()
    return jsonify({'message': 'Product added to cart successfully'})

@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    """Retrieve the cart contents for a specific user."""
    db = get_db()
    cur = db.execute('''
        SELECT carts.id, products.name, products.price, carts.quantity
        FROM carts
        JOIN products ON carts.product_id = products.id
        WHERE carts.user_id = ?
    ''', (user_id,))
    items = cur.fetchall()
    return jsonify([dict(item) for item in items])

@app.route('/test', methods=['GET'])
def test_api():
    """
    A simple test route that:
      - Retrieves product details for product 1
      - Adds product 1 to user 1's cart (quantity of 2)
      - Retrieves user 1's cart
    """
    # Get product info (for testing purposes)
    product_response = get_product(1).json

    # Use the Flask test client to simulate adding to the cart
    with app.test_client() as client:
        add_response = client.post('/cart/add', json={'user_id': 1, 'product_id': 1, 'quantity': 1})
        cart_response = client.get('/cart/1')

    return jsonify({
        'product': product_response,
        'add_to_cart_response': add_response.json,
        'cart': cart_response.json
    })

if __name__ == '__main__':
    # On startup, initialize the database and populate sample data
    with app.app_context():
        init_db()
        populate_dummy_data()
    # Start the Flask server
    app.run(debug=True)
