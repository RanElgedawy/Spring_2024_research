from flask import Flask, request, jsonify, g
import sqlite3

DATABASE = 'ecommerce.db'

app = Flask(__name__)

# --- Database functions ---

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initializes the database with tables for products and carts, and adds sample products."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS cart")

        # Create products table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        ''')
        
        # Create cart table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # Insert sample product data if the products table is empty
        cursor.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()["count"] == 0:
            sample_products = [
                (1, "Widget A", "High quality widget", 19.99, 10),
                (2, "Widget B", "Economy widget", 9.99, 0),  # out-of-stock
                (3, "Widget C", "Premium widget", 29.99, 5)
            ]
            cursor.executemany(
                "INSERT INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)",
                sample_products
            )
        
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection on app context teardown."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- API Endpoints ---

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Retrieve product information by product ID.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    # Convert sqlite3.Row to dict
    return jsonify(dict(product)), 200

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """
    Add product to authenticated user's cart.
    Expects JSON payload with keys:
      - product_id: int
      - quantity: int (optional, default=1)
    
    User is identified by X-User-Id header.
    """
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'error': 'Missing X-User-Id header'}), 400

    data = request.get_json()
    if not data or 'product_id' not in data:
        return jsonify({'error': 'Invalid request, missing product_id'}), 400

    product_id = data['product_id']
    quantity = data.get('quantity', 1)
    if quantity < 1:
        return jsonify({'error': 'Quantity must be at least 1'}), 400

    db = get_db()
    cursor = db.cursor()

    # Get product information
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if product is None:
        return jsonify({'error': 'Product not found'}), 404

    # Check if sufficient stock is available
    if product['stock'] < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400

    # Deduct stock from product
    new_stock = product['stock'] - quantity
    cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))

    # Check if the product already exists in the user's cart
    cursor.execute("SELECT * FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    cart_item = cursor.fetchone()
    if cart_item:
        # update quantity
        new_quantity = cart_item['quantity'] + quantity
        cursor.execute("UPDATE cart SET quantity = ? WHERE id = ?", (new_quantity, cart_item['id']))
    else:
        cursor.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
            (user_id, product_id, quantity)
        )

    db.commit()

    return jsonify({'message': 'Product added to cart successfully', 'remaining_stock': new_stock}), 200

# --- Testing functionality ---

def run_tests():
    """
    Runs a few tests using Flask's test client to verify functionality.
    """
    with app.test_client() as client:
        # Test retrieving a product that exists
        response = client.get('/products/1')
        print("GET /products/1:", response.status_code, response.get_json())

        # Test retrieving a product that does not exist
        response = client.get('/products/999')
        print("GET /products/999:", response.status_code, response.get_json())

        # Test adding product to cart with sufficient stock
        headers = {"Content-Type": "application/json", "X-User-Id": "user123"}
        payload = {"product_id": 1, "quantity": 2}
        response = client.post('/cart/add', json=payload, headers=headers)
        print("POST /cart/add (sufficient stock):", response.status_code, response.get_json())

        # Test adding product to cart with insufficient stock (widget B has 0 stock)
        payload = {"product_id": 2, "quantity": 1}
        response = client.post('/cart/add', json=payload, headers=headers)
        print("POST /cart/add (insufficient stock):", response.status_code, response.get_json())

if __name__ == '__main__':
    # Initialize the database and create tables
    init_db()
    print("Database initialized with sample data.")
    
    # Uncomment the next line to run the Flask server
    app.run(debug=True)
    
    # For demonstration purposes, run tests using the test client
    run_tests()
