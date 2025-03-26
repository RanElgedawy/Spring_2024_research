from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Function to connect to the SQLite database
def connect_db():
    conn = sqlite3.connect('your_database.db')  # Adjust the file path as needed
    return conn


# Create tables in the database
def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE users (
                        id INTEGER PRIMARY KEY,
                        username TEXT,
                        address TEXT,
                        card_number TEXT,
                        expiry_date TEXT
                    )''')

    cursor.execute('''CREATE TABLE cart (
                        user_id INTEGER,
                        product_id INTEGER,
                        name TEXT,
                        quantity INTEGER,
                        price REAL
                    )''')

    cursor.execute('''CREATE TABLE orders (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        shipping_address TEXT,
                        total_amount REAL,
                        status TEXT
                    )''')

    cursor.execute('''CREATE TABLE order_items (
                        order_id INTEGER,
                        product_id INTEGER,
                        name TEXT,
                        quantity INTEGER,
                        price REAL
                    )''')
    conn.commit()

# Simulate payment process
def process_payment(card_number, expiry_date, total_amount):
    # This is a placeholder function. You can replace it with actual payment processing logic.
    # For demonstration purposes, we assume the payment is successful if the card number and expiry date are provided.
    if card_number and expiry_date:
        return True
    else:
        return False

def add_user():
    if request.method == 'POST':
        data = request.json
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, address, card_number, expiry_date) VALUES (?, ?, ?, ?)",
                       (data['username'], data['address'], data['card_number'], data['expiry_date']))
        conn.commit()
        conn.close()
        return jsonify({"message": "User added successfully"}), 201
    else:
        return jsonify({"error": "Method not allowed"}), 405

app.add_url_rule('/add_user', 'add_user', add_user, methods=['POST'])


# Endpoint to handle adding an item to the cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.json
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cart (user_id, product_id, name, quantity, price) VALUES (?, ?, ?, ?, ?)",
                   (data['user_id'], data['product_id'], data['name'], data['quantity'], data['price']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Item added to cart successfully"}), 201

# Endpoint to handle checkout process
@app.route('/checkout', methods=['POST'])
def checkout():
    # Get user's ID from request (assuming authentication has already happened)
    user_id = request.json.get('user_id')

    # Check if the user is logged in
    if user_id is None:
        return jsonify({"error": "User not logged in"}), 401

    # Retrieve user's cart items
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, quantity, price FROM cart WHERE user_id=?", (user_id,))
    cart_items = cursor.fetchall()

    # Retrieve user's shipping address and card information
    cursor.execute("SELECT address, card_number, expiry_date FROM users WHERE id=?", (user_id,))
    user_info = cursor.fetchone()

    if user_info is None:
        return jsonify({"error": "User not found"}), 404

    shipping_address, card_number, expiry_date = user_info

    # Calculate total amount including shipping fee
    total_amount = sum(item[3] for item in cart_items) + 20

    # Simulate payment process
    if not process_payment(card_number, expiry_date, total_amount):
        return jsonify({"error": "Payment failed"}), 400

    # Assuming payment is successful, record the order
    cursor.execute("INSERT INTO orders (user_id, shipping_address, total_amount, status) VALUES (?, ?, ?, ?)",
                   (user_id, shipping_address, total_amount, 'Submitted'))
    order_id = cursor.lastrowid

    # Record individual items in the order
    for item in cart_items:
        cursor.execute("INSERT INTO order_items (order_id, product_id, name, quantity, price) VALUES (?, ?, ?, ?, ?)",
                       (order_id, item[0], item[1], item[2], item[3]))

    # Commit changes and close connection
    conn.commit()
    conn.close()

    return jsonify({"message": "Order placed successfully!", "order_id": order_id}), 200

if __name__ == '__main__':
    conn = connect_db()
    create_tables(conn)
    app.run(debug=True)