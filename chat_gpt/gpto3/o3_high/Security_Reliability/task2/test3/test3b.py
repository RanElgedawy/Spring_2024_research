import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # enables name-based access to columns
    return conn

def init_db():
    """Initializes the database, creates tables if they do not exist, and inserts sample data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table (assume user data already exists in production)
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS cart")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL
        )
    ''')

    # Create products table (assume product data already exists in production)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            stock INTEGER NOT NULL
        )
    ''')

    # Create cart table to store user cart items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    conn.commit()

    # Insert sample data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        sample_users = [
            (1, "Alice"),
            (2, "Bob")
        ]
        cursor.executemany("INSERT INTO users (id, username) VALUES (?, ?)", sample_users)

    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_products = [
            (1, "Product A", "A great product", 9.99, 10),
            (2, "Product B", "Another product", 19.99, 0),   # Out of stock
            (3, "Product C", "A premium product", 29.99, 5)
        ]
        cursor.executemany("INSERT INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)", sample_products)

    conn.commit()
    conn.close()

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Retrieves product information by product ID."""
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()

    if product is None:
        return jsonify({'error': 'Product not found'}), 404

    # Convert row to dict
    product_data = dict(product)
    return jsonify(product_data)

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """
    Adds a product to a user's cart.
    Expected JSON payload:
      {
         "user_id": <int>,
         "product_id": <int>,
         "quantity": <int>   // optional, defaults to 1 if not provided
      }
    The endpoint checks that:
      - The user exists.
      - The product exists.
      - The product has sufficient stock.
    It then either creates a new cart entry or updates an existing one,
    and updates the product stock accordingly.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id or not product_id:
        return jsonify({'error': 'Missing user_id or product_id'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if product exists and has enough stock
    product = cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404
    if product['stock'] < quantity:
        conn.close()
        return jsonify({'error': 'Product not in stock or insufficient quantity'}), 400

    # Check if user exists
    user = cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    # Check if the cart already has this product for the user
    cart_entry = cursor.execute("SELECT * FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id)).fetchone()
    if cart_entry:
        new_quantity = cart_entry['quantity'] + quantity
        cursor.execute("UPDATE cart SET quantity = ? WHERE id = ?", (new_quantity, cart_entry['id']))
    else:
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))

    # Update the product's stock
    new_stock = product['stock'] - quantity
    cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Product added to cart successfully'})

@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    """Retrieves all cart items for a given user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cart_items = cursor.execute(
        "SELECT cart.id, products.name, cart.quantity FROM cart "
        "JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?",
        (user_id,)
    ).fetchall()
    conn.close()

    # Convert each row to a dict
    items = [dict(item) for item in cart_items]
    return jsonify(items)

if __name__ == '__main__':
    init_db()
    print("API server starting. Test endpoints using curl, Postman, etc.")
    app.run(debug=True)
