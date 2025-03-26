from flask import Flask, request, jsonify
import sqlite3
import json

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# --- Database Initialization ---

def get_db():
    db = getattr(app, '_database', None)
    if db is None:
        db = app._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # To access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(app, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Create users table if it doesn't exist
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                -- Add other user details as needed
                password TEXT NOT NULL -- In a real app, hash passwords!
            )
        """)

        # Create products table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        """)

        # Create cart table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)
        db.commit()

def populate_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Add a sample user (for testing)
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, password) VALUES (?, ?, ?)", (1, 'testuser', 'password'))

        # Add some sample products
        products = [
            ('Awesome T-Shirt', 'A comfortable and stylish t-shirt', 25.99, 100),
            ('Cool Mug', 'A ceramic mug for your favorite beverage', 12.50, 50),
            ('Tech Gadget', 'A cutting-edge electronic device', 199.00, 10)
        ]
        cursor.executemany("INSERT OR IGNORE INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)", products)

        db.commit()

# Initialize the database and populate with sample data
init_db()
populate_db()

# --- API Endpoints ---

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT product_id, name, description, price, stock FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()

    if product:
        return jsonify(dict(product)), 200
    return jsonify({'message': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    if not all([user_id, product_id, quantity]):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        user_id = int(user_id)
        product_id = int(product_id)
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({'message': 'Quantity must be greater than zero'}), 400
    except ValueError:
        return jsonify({'message': 'Invalid data type for user_id, product_id, or quantity'}), 400

    db = get_db()
    cursor = db.cursor()

    # Check if the user exists (assuming authentication happened elsewhere)
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Check if the product exists and has enough stock
    cursor.execute("SELECT name, stock FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    if product['stock'] < quantity:
        return jsonify({'message': f'Not enough stock for {product["name"]}. Available stock: {product["stock"]}'}), 400

    # Add the product to the user's cart
    cursor.execute("""
        INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)
    """, (user_id, product_id, quantity))
    db.commit()

    return jsonify({'message': f'{quantity} of {product["name"]} added to cart for user {user_id}'}), 201

# --- Functionality to test the API ---

def test_api():
    import requests

    base_url = "http://127.0.0.1:5000"

    print("\n--- Testing Get Product ---")
    product_id_to_get = 1
    get_product_url = f"{base_url}/products/{product_id_to_get}"
    response = requests.get(get_product_url)
    print(f"GET {get_product_url}: Status Code {response.status_code}")
    print(f"Response: {response.json()}")

    print("\n--- Testing Add to Cart ---")
    add_to_cart_url = f"{base_url}/cart/add"
    payload = {
        "user_id": 1,
        "product_id": 2,
        "quantity": 2
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(add_to_cart_url, headers=headers, json=payload)
    print(f"POST {add_to_cart_url}: Status Code {response.status_code}")
    print(f"Response: {response.json()}")

    print("\n--- Testing Add to Cart (Not Enough Stock) ---")
    payload_no_stock = {
        "user_id": 1,
        "product_id": 3,
        "quantity": 15  # Assuming product 3 has only 10 stock
    }
    response = requests.post(add_to_cart_url, headers=headers, json=payload_no_stock)
    print(f"POST {add_to_cart_url} (No Stock): Status Code {response.status_code}")
    print(f"Response: {response.json()}")

    print("\n--- Testing Add to Cart (Invalid User) ---")
    payload_invalid_user = {
        "user_id": 999,
        "product_id": 1,
        "quantity": 1
    }
    response = requests.post(add_to_cart_url, headers=headers, json=payload_invalid_user)
    print(f"POST {add_to_cart_url} (Invalid User): Status Code {response.status_code}")
    print(f"Response: {response.json()}")

    print("\n--- Testing Add to Cart (Invalid Product) ---")
    payload_invalid_product = {
        "user_id": 1,
        "product_id": 999,
        "quantity": 1
    }
    response = requests.post(add_to_cart_url, headers=headers, json=payload_invalid_product)
    print(f"POST {add_to_cart_url} (Invalid Product): Status Code {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == '__main__':
    # Run the Flask development server
    app.run(debug=True)

    # After the server starts (or in a separate terminal), you can run the tests
    # To run the tests from this script, you would typically do something like:
    # test_api()
    # However, running the Flask app blocks further execution.
    # Instructions on how to test are printed below.