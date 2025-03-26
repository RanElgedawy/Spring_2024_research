from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Helper function to get a database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

# Helper function to close the database connection
def close_db(conn):
    if conn:
        conn.close()

# Helper function to initialize the database with tables and some sample data
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS carts")

    # Create users table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
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

    # Create carts table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            UNIQUE (user_id, product_id)
        )
    """)

    # Insert some sample users if the table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username) VALUES (?)", ('user1',))
        cursor.execute("INSERT INTO users (username) VALUES (?)", ('user2',))

    # Insert some sample products if the table is empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       ('Laptop', 'High-performance laptop', 1200.00, 10))
        cursor.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       ('Mouse', 'Wireless ergonomic mouse', 25.00, 50))
        cursor.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       ('Keyboard', 'Mechanical gaming keyboard', 75.00, 20))
        cursor.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       ('Monitor', '27-inch 4K monitor', 350.00, 5))

    conn.commit()
    close_db(conn)

# Run database initialization when the script starts
with app.app_context():
    init_db()

# --- API Endpoints ---

# Endpoint to retrieve product information by product ID
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    product = cursor.execute("SELECT product_id, name, description, price, stock FROM products WHERE product_id = ?", (product_id,)).fetchone()
    close_db(conn)

    if product:
        return jsonify(dict(product))
    return jsonify({'message': 'Product not found'}), 404

# Endpoint to add a product to the user's cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)  # Default quantity is 1

    if not user_id or not product_id:
        return jsonify({'message': 'Missing user_id or product_id'}), 400

    if not isinstance(user_id, int) or not isinstance(product_id, int) or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'message': 'Invalid input types or quantity'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if the user exists
    user = cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user:
        close_db(conn)
        return jsonify({'message': 'User not found'}), 404

    # Check if the product exists and has enough stock
    product = cursor.execute("SELECT name, price, stock FROM products WHERE product_id = ?", (product_id,)).fetchone()
    if not product:
        close_db(conn)
        return jsonify({'message': 'Product not found'}), 404
    if product['stock'] < quantity:
        close_db(conn)
        return jsonify({'message': f'Not enough stock for product: {product["name"]}'}), 400

    try:
        # Check if the product is already in the user's cart
        existing_cart_item = cursor.execute("SELECT quantity FROM carts WHERE user_id = ? AND product_id = ?", (user_id, product_id)).fetchone()

        if existing_cart_item:
            new_quantity = existing_cart_item['quantity'] + quantity
            cursor.execute("UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?", (new_quantity, user_id, product_id))
        else:
            cursor.execute("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))

        # Optionally, you might want to decrease the product stock here or in a separate process after checkout
        # For this example, we'll assume stock management happens elsewhere or after order confirmation.

        conn.commit()
        close_db(conn)
        return jsonify({'message': f'Added {quantity} of product "{product["name"]}" to user {user_id}\'s cart'}), 201
    except sqlite3.IntegrityError:
        close_db(conn)
        return jsonify({'message': 'Could not add product to cart (integrity error)'}), 400
    except Exception as e:
        close_db(conn)
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

# --- Testing the API ---
if __name__ == '__main__':
    import requests

    # Start the Flask development server
    app.run(debug=True)

    # --- Example Usage (will not run automatically when Flask server is running) ---
    # To test, open another terminal and run these commands:

    # # Get product information
    # response_product = requests.get('http://127.0.0.1:5000/products/1')
    # print("Get Product Response:", response_product.json())

    # # Add product to cart (assuming user_id 1 exists and product_id 2 has stock)
    # data_add_to_cart = {'user_id': 1, 'product_id': 2, 'quantity': 3}
    # response_add_to_cart = requests.post('http://127.0.0.1:5000/cart/add', json=data_add_to_cart)
    # print("Add to Cart Response:", response_add_to_cart.json())

    # # Try to add more than the available stock
    # data_add_to_cart_exceed_stock = {'user_id': 1, 'product_id': 4, 'quantity': 10}
    # response_add_to_cart_exceed_stock = requests.post('http://127.0.0.1:5000/cart/add', json=data_add_to_cart_exceed_stock)
    # print("Add to Cart (Exceed Stock) Response:", response_add_to_cart_exceed_stock.json())

    # # Try to add to a non-existent user's cart
    # data_add_to_cart_invalid_user = {'user_id': 999, 'product_id': 2, 'quantity': 1}
    # response_add_to_cart_invalid_user = requests.post('http://127.0.0.1:5000/cart/add', json=data_add_to_cart_invalid_user)
    # print("Add to Cart (Invalid User) Response:", response_add_to_cart_invalid_user.json())