from flask import Flask, request, jsonify
import sqlite3
import json

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def close_db(conn):
    if conn:
        conn.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        close_db(db)

# Initialize the database when the application starts
with app.app_context():
    init_db()

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db()
    product = conn.execute('SELECT id, name, description, price, stock FROM products WHERE id = ?', (product_id,)).fetchone()
    close_db(conn)

    if product:
        return jsonify(dict(product))
    return jsonify({'message': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)

    if not user_id or not product_id:
        return jsonify({'message': 'Missing user_id or product_id'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if the product exists and has enough stock
    product = cursor.execute('SELECT name, price, stock FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        close_db(conn)
        return jsonify({'message': 'Product not found'}), 404
    if product['stock'] < quantity:
        close_db(conn)
        return jsonify({'message': f'Not enough stock for product: {product["name"]}'}), 400

    # Check if the product is already in the user's cart
    cart_item = cursor.execute('SELECT quantity FROM carts WHERE user_id = ? AND product_id = ?', (user_id, product_id)).fetchone()

    if cart_item:
        new_quantity = cart_item['quantity'] + quantity
        cursor.execute('UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?', (new_quantity, user_id, product_id))
    else:
        cursor.execute('INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))

    # Optionally, you might want to decrease the product stock here,
    # depending on your business logic. For simplicity, we'll skip it in this example.

    conn.commit()
    close_db(conn)
    return jsonify({'message': f'Added {quantity} of {product["name"]} to user {user_id}\'s cart'}), 201

if __name__ == '__main__':
    # Create the database schema if it doesn't exist
    init_db()

    # Example data insertion for testing
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Insert sample users
        cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (1, 'user1'))
        cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (2, 'user2'))

        # Insert sample products
        cursor.execute("INSERT OR IGNORE INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)",
                       (101, 'Laptop', 'High-performance laptop', 1200.00, 10))
        cursor.execute("INSERT OR IGNORE INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)",
                       (102, 'Mouse', 'Wireless ergonomic mouse', 25.00, 50))
        cursor.execute("INSERT OR IGNORE INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)",
                       (103, 'Keyboard', 'Mechanical gaming keyboard', 75.00, 5))

        db.commit()
        close_db(db)

    print("API running on http://127.0.0.1:5000")
    print("\n--- How to test ---")
    print("\n1. Retrieve product information (replace <product_id> with 101, 102, or 103):")
    print("   - Open a browser or use a tool like curl/Postman and go to: http://127.0.0.1:5000/products/<product_id>")
    print("\n2. Add product to cart (using curl):")
    print("   - To add product with ID 101 (Laptop) with quantity 2 for user ID 1:")
    print("     ```bash")
    print("     curl -X POST -H 'Content-Type: application/json' -d '{\"user_id\": 1, \"product_id\": 101, \"quantity\": 2}' [http://127.0.0.1:5000/cart/add](http://127.0.0.1:5000/cart/add)")
    print("     ```")
    print("   - To add product with ID 102 (Mouse) with default quantity 1 for user ID 1:")
    print("     ```bash")
    print("     curl -X POST -H 'Content-Type: application/json' -d '{\"user_id\": 1, \"product_id\": 102}' [http://127.0.0.1:5000/cart/add](http://127.0.0.1:5000/cart/add)")
    print("     ```")
    print("\nRemember to have Flask installed (`pip install Flask`).")
    app.run(debug=True)