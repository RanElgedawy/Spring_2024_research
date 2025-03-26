from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the tables for users, products, carts, and orders
def init_db():
    conn = get_db_connection()
    with conn:
        conn.executescript('''
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS carts;
        DROP TABLE IF EXISTS orders;
                           
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            shipping_address TEXT,
            payment_info TEXT
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL
        );

        CREATE TABLE IF NOT EXISTS carts (
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total_price REAL,
            shipping_fee REAL,
            order_status TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        ''')
    conn.close()

# Fetch user's cart details
def get_cart_details(user_id):
    conn = get_db_connection()
    cart_items = conn.execute('''
        SELECT p.id, p.name, p.price, c.quantity 
        FROM products p 
        JOIN carts c ON p.id = c.product_id 
        WHERE c.user_id = ?''', (user_id,)).fetchall()
    conn.close()
    return cart_items

# Fetch user's shipping address and payment info from the profile
def get_user_profile(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

# Insert a new order into the database
def create_order(user_id, total_price, shipping_fee):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO orders (user_id, total_price, shipping_fee, order_status) 
        VALUES (?, ?, ?, ?)''', (user_id, total_price, shipping_fee, 'Success'))
    conn.commit()
    conn.close()

# Checkout endpoint to process the order
@app.route('/checkout', methods=['POST'])
def checkout():
    user_id = request.json['user_id']

    # Retrieve user's profile (shipping address, payment info)
    user = get_user_profile(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Retrieve cart details
    cart_items = get_cart_details(user_id)
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400

    # Calculate the total price
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    shipping_fee = 20.00  # Apply flat $20 shipping fee
    total_price_with_shipping = total_price + shipping_fee

    # (Mock) Process payment with user's payment info
    payment_successful = True  # Simulate successful payment

    if payment_successful:
        # Record the order in the database
        create_order(user_id, total_price_with_shipping, shipping_fee)
        return jsonify({
            'message': 'Order placed successfully!',
            'total_price': total_price_with_shipping,
            'shipping_address': user['shipping_address']
        }), 200
    else:
        return jsonify({'error': 'Payment failed'}), 400

# Test route to verify database and test functionality
@app.route('/test', methods=['GET'])
def test():
    # Insert a sample user, products, and cart data to test
    conn = get_db_connection()
    with conn:
        conn.executescript('''
        INSERT INTO users (username, email, shipping_address, payment_info) 
        VALUES ('johndoe', 'john@example.com', '123 Elm St', 'VISA-XXXX');

        INSERT INTO products (name, price) 
        VALUES ('Laptop', 999.99), ('Phone', 499.99);

        INSERT INTO carts (user_id, product_id, quantity) 
        VALUES (1, 1, 1), (1, 2, 2);
        ''')
    conn.close()
    return jsonify({'message': 'Test data inserted successfully'}), 200

if __name__ == '__main__':
    init_db()  # Initialize the database and tables
    app.run(debug=True)
