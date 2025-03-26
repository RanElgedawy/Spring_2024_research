import sqlite3
from flask import Flask, request, jsonify, g
import sys

DATABASE = 'ecommerce.db'
app = Flask(__name__)

# --- Database Connection Helpers ---

def get_db():
    """Opens a new database connection if there isn't one for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database by creating tables if they don't exist and inserting sample data."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Create products table
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS carts")
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            stock INTEGER NOT NULL
        )
    ''')
    # Create carts table (each user can have one entry per product)
    c.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            UNIQUE(user_id, product_id)
        )
    ''')
    # Insert sample products if none exist
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        products = [
            (1, 'Product A', 'Description for Product A', 9.99, 10),
            (2, 'Product B', 'Description for Product B', 19.99, 5),
            (3, 'Product C', 'Description for Product C', 29.99, 0)  # Out-of-stock product
        ]
        c.executemany(
            "INSERT INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)",
            products
        )
    conn.commit()
    conn.close()

# --- API Endpoints ---

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Retrieves product information by product ID.
    Uses a parameterized query to prevent SQL injection.
    """
    db = get_db()
    c = db.cursor()
    c.execute("SELECT id, name, description, price, stock FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    if product:
        return jsonify(dict(product)), 200
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """
    Adds a product to a user's cart if the product is in stock.
    Expects JSON data with 'user_id', 'product_id', and 'quantity'.
    Uses parameterized queries for all database operations.
    """
    data = request.get_json()
    if not data or 'user_id' not in data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Missing data: user_id, product_id, and quantity are required'}), 400

    user_id = data['user_id']
    product_id = data['product_id']
    quantity = data['quantity']

    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400

    db = get_db()
    c = db.cursor()
    # Check if the product exists and has sufficient stock
    c.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    available_stock = product['stock']
    if available_stock < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    try:
        # Attempt to insert a new cart entry
        c.execute("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
                  (user_id, product_id, quantity))
    except sqlite3.IntegrityError:
        # If an entry already exists for this user and product, update the quantity instead
        c.execute("UPDATE carts SET quantity = quantity + ? WHERE user_id = ? AND product_id = ?",
                  (quantity, user_id, product_id))
    # Update product stock by reducing the available quantity
    c.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
    db.commit()
    return jsonify({'message': 'Product added to cart successfully'}), 200

# --- Testing Functionality ---

def run_tests():
    """
    Runs a few basic tests to verify that the API endpoints work as expected.
    Uses Flask's built-in test client.
    """
    with app.test_client() as client:
        # Test retrieving a product that exists
        response = client.get('/product/1')
        print('GET /product/1:', response.status_code, response.get_json())

        # Test retrieving an out-of-stock product
        response = client.get('/product/3')
        print('GET /product/3:', response.status_code, response.get_json())

        # Test adding an in-stock product to the cart
        payload = {'user_id': 1, 'product_id': 1, 'quantity': 3}
        response = client.post('/cart/add', json=payload)
        print('POST /cart/add (in stock):', response.status_code, response.get_json())

        # Test trying to add an out-of-stock product
        payload = {'user_id': 1, 'product_id': 3, 'quantity': 1}
        response = client.post('/cart/add', json=payload)
        print('POST /cart/add (out of stock):', response.status_code, response.get_json())

        # Test adding a product with insufficient stock
        payload = {'user_id': 2, 'product_id': 2, 'quantity': 10}
        response = client.post('/cart/add', json=payload)
        print('POST /cart/add (insufficient stock):', response.status_code, response.get_json())

        # Check updated stock for product 1 after adding to cart
        response = client.get('/product/1')
        print('GET /product/1 after addition:', response.status_code, response.get_json())

if __name__ == '__main__':
    # Initialize the database and tables (and sample data) on startup
    init_db()
    # If the script is run with the argument 'test', run the test function instead of starting the server
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_tests()
    else:
        app.run(debug=True)
