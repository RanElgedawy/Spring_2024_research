from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    cur.close()

# --- API Endpoints ---

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Retrieves product information by product ID."""
    product = query_db('SELECT id, name, description, price, stock FROM products WHERE id = ?', (product_id,), one=True)
    if product:
        return jsonify(dict(product))
    return jsonify({'error': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Adds a product to the user's cart."""
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id or not product_id:
        return jsonify({'error': 'Missing user_id or product_id'}), 400

    if quantity <= 0:
        return jsonify({'error': 'Quantity must be greater than zero'}), 400

    # Check if the product exists and has enough stock
    product = query_db('SELECT id, name, price, stock FROM products WHERE id = ?', (product_id,), one=True)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product['stock'] < quantity:
        return jsonify({'error': f'Not enough stock for product {product_id}'}), 400

    # Check if the product is already in the user's cart
    existing_cart_item = query_db('SELECT id, quantity FROM carts WHERE user_id = ? AND product_id = ?', (user_id, product_id), one=True)

    if existing_cart_item:
        new_quantity = existing_cart_item['quantity'] + quantity
        execute_db('UPDATE carts SET quantity = ? WHERE id = ?', (new_quantity, existing_cart_item['id']))
    else:
        execute_db('INSERT INTO carts (user_id, product_id, quantity, price_at_add) VALUES (?, ?, ?, ?)', (user_id, product_id, quantity, product['price']))

    # Optionally, decrease the product stock (depending on your business logic)
    new_stock = product['stock'] - quantity
    execute_db('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product_id))

    return jsonify({'message': f'Added {quantity} of product {product_id} to user {user_id}\'s cart'}), 201

# --- Initialization and Testing ---

if __name__ == '__main__':
    # Create the database and tables if they don't exist
    with app.app_context():
        init_db()

    # Example usage for testing (you can run this in a separate Python script or using curl)
    import requests
    import json

    BASE_URL = 'http://127.0.0.1:5000'

    # --- Helper functions for testing ---

    def create_test_data():
        conn = get_db()
        cursor = conn.cursor()

        # Create users table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        ''')
        # Add some test users
        cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (1, 'user1'))
        cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (2, 'user2'))

        # Create products table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        ''')
        # Add some test products
        cursor.execute("INSERT OR IGNORE INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)", (1, 'Laptop', 'Powerful laptop', 1200.00, 10))
        cursor.execute("INSERT OR IGNORE INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)", (2, 'Mouse', 'Wireless mouse', 25.00, 50))
        cursor.execute("INSERT OR IGNORE INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)", (3, 'Keyboard', 'Mechanical keyboard', 75.00, 0))

        # Create carts table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price_at_add REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        conn.commit()
        conn.close()
        print("Test data created/verified.")

    create_test_data()

    print("\n--- Testing API ---")

    # Test get_product
    print("\n--- Testing GET /products/1 ---")
    response = requests.get(f'{BASE_URL}/products/1')
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

    print("\n--- Testing GET /products/3 (out of stock) ---")
    response = requests.get(f'{BASE_URL}/products/3')
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

    print("\n--- Testing POST /cart/add (add product 2 for user 1) ---")
    payload = {'user_id': 1, 'product_id': 2, 'quantity': 2}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f'{BASE_URL}/cart/add', data=json.dumps(payload), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

    print("\n--- Testing POST /cart/add (add product 1 for user 1) ---")
    payload = {'user_id': 1, 'product_id': 1, 'quantity': 1}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f'{BASE_URL}/cart/add', data=json.dumps(payload), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

    print("\n--- Testing POST /cart/add (add more of product 2 for user 1) ---")
    payload = {'user_id': 1, 'product_id': 2, 'quantity': 3}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f'{BASE_URL}/cart/add', data=json.dumps(payload), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

    print("\n--- Testing POST /cart/add (try to add out of stock product 3 for user 2) ---")
    payload = {'user_id': 2, 'product_id': 3, 'quantity': 1}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f'{BASE_URL}/cart/add', data=json.dumps(payload), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

    print("\n--- Testing POST /cart/add (try to add more than available stock for product 1 for user 2) ---")
    response_get_product1 = requests.get(f'{BASE_URL}/products/1')
    current_stock_product1 = response_get_product1.json().get('stock', 0)
    payload = {'user_id': 2, 'product_id': 1, 'quantity': current_stock_product1 + 1}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f'{BASE_URL}/cart/add', data=json.dumps(payload), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

    # Run the Flask development server
    app.run(debug=True)