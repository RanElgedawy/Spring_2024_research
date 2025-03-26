from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE_PRODUCTS = 'products.db'
DATABASE_USERS = 'users.db'
DATABASE_CART = 'cart.db'

# --- Database Initialization ---

def create_tables():
    """Creates necessary tables in the databases if they don't exist."""
    conn_products = sqlite3.connect(DATABASE_PRODUCTS)
    cursor_products = conn_products.cursor()
    cursor_products.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    conn_products.commit()
    conn_products.close()

    conn_users = sqlite3.connect(DATABASE_USERS)
    cursor_users = conn_users.cursor()
    cursor_users.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    ''')
    conn_users.commit()
    conn_users.close()

    conn_cart = sqlite3.connect(DATABASE_CART)
    cursor_cart = conn_cart.cursor()
    cursor_cart.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            PRIMARY KEY (user_id, product_id)
        )
    ''')
    conn_cart.commit()
    conn_cart.close()

def populate_initial_data():
    """Populates the databases with some initial data for testing."""
    conn_products = sqlite3.connect(DATABASE_PRODUCTS)
    cursor_products = conn_products.cursor()
    products = [
        ('Laptop', 'High-performance laptop', 1200.00, 10),
        ('Mouse', 'Wireless ergonomic mouse', 25.00, 50),
        ('Keyboard', 'Mechanical gaming keyboard', 75.00, 25),
        ('Monitor', '27-inch 4K monitor', 350.00, 15),
    ]
    cursor_products.executemany("INSERT OR IGNORE INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)", products)
    conn_products.commit()
    conn_products.close()

    conn_users = sqlite3.connect(DATABASE_USERS)
    cursor_users = conn_users.cursor()
    users = [
        ('user1',),
        ('user2',),
    ]
    cursor_users.executemany("INSERT OR IGNORE INTO users (username) VALUES (?)", users)
    conn_users.commit()
    conn_users.close()

create_tables()
populate_initial_data()

# --- Helper Functions for Database Operations ---

def get_db_connection(db_file):
    """Establishes a database connection."""
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def get_product_by_id(product_id):
    """Retrieves product information by its ID."""
    conn = get_db_connection(DATABASE_PRODUCTS)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price, stock FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

def get_user_by_id(user_id):
    """Retrieves user information by its ID."""
    conn = get_db_connection(DATABASE_USERS)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_product_to_cart(user_id, product_id, quantity):
    """Adds a product to the user's cart."""
    conn_products = get_db_connection(DATABASE_PRODUCTS)
    cursor_products = conn_products.cursor()
    cursor_products.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    product = cursor_products.fetchone()

    if not product:
        conn_products.close()
        return "Product not found", 404

    if product['stock'] < quantity:
        conn_products.close()
        return "Insufficient stock", 400

    conn_cart = get_db_connection(DATABASE_CART)
    cursor_cart = conn_cart.cursor()
    try:
        cursor_cart.execute("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))
        conn_cart.commit()

        # Update product stock
        new_stock = product['stock'] - quantity
        cursor_products.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
        conn_products.commit()
        conn_products.close()
        conn_cart.close()
        return "Product added to cart successfully", 201
    except sqlite3.IntegrityError:
        # Handle case where the product is already in the cart (you might want to update quantity instead)
        conn_products.close()
        conn_cart.close()
        return "Product already in cart", 409

# --- API Endpoints ---

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """API endpoint to retrieve product information by ID."""
    product = get_product_by_id(product_id)
    if product:
        return jsonify(dict(product)), 200
    return jsonify({'message': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """API endpoint to add a product to the user's cart."""
    data = request.get_json()
    if not data or 'product_id' not in data or 'quantity' not in data or 'user_id' not in data:
        return jsonify({'message': 'Missing required parameters (product_id, quantity, user_id)'}), 400

    product_id = data['product_id']
    quantity = data['quantity']
    user_id = data['user_id']  # In a real application, you'd get this from the user's session or token

    # For demonstration purposes, let's check if the user exists
    if not get_user_by_id(user_id):
        return jsonify({'message': 'User not found'}), 404

    message, status_code = add_product_to_cart(user_id, product_id, quantity)
    return jsonify({'message': message}), status_code

# --- Testing the API ---

if __name__ == '__main__':
    print("Server is running. You can test the API using the following examples:")
    print("  - To get product information: curl http://127.0.0.1:5000/products/1")
    print("  - To add a product to the cart (replace user_id, product_id, quantity):")
    print("    curl -X POST -H 'Content-Type: application/json' -d '{\"user_id\": 1, \"product_id\": 2, \"quantity\": 2}' http://127.0.0.1:5000/cart/add")
    print("\nMake sure you have Flask installed (`pip install Flask`).")
    app.run(debug=True)