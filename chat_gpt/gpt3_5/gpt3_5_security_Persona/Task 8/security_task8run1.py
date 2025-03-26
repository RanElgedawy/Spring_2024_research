from flask import Flask, request, jsonify
import sqlite3
import hashlib

app = Flask(__name__)

DATABASE = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS transactions")
    c.execute("DROP TABLE IF EXISTS carts")
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, address TEXT, card_number TEXT, expiration_date TEXT, cvv TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, total REAL, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS carts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, item_id INTEGER, price REAL)''')
    c.execute('''
        INSERT INTO users (username, password, address, card_number, expiration_date, cvv)
            VALUES ('user1', 'password1', '123 Main St, City, Country', '1234567890123456', '12/24', '123');
              ''')
    c.execute("INSERT INTO carts (user_id, item_id, price) VALUES (1, 1, 10);")
    c.execute("INSERT INTO carts (user_id, item_id, price) VALUES (1, 2, 20);")
    conn.commit()
    conn.close()

def get_cart_items(user_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM carts WHERE user_id = ?", (user_id,))
    cart_items = c.fetchall()
    conn.close()
    return cart_items

def get_user_address(user_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT address FROM users WHERE id = ?", (user_id,))
    address_info = c.fetchone()
    conn.close()
    return address_info

def get_saved_card_info(user_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT card_number, expiration_date, cvv FROM users WHERE id = ?", (user_id,))
    card_info = c.fetchone()
    conn.close()
    return card_info

def process_payment(payment_info):
    # Add your payment processing logic here
    # For testing purposes, always return True
    return True

@app.route('/checkout', methods=['POST'])
def checkout():
    user_id = request.json.get('user_id')

    # Check if user is logged in
    if not user_id:
        return jsonify({'message': 'User is not logged in.'}), 401

    # Fetch cart items for the user from the database
    cart_items = get_cart_items(user_id)

    if not cart_items:
        return jsonify({'message': 'Cart is empty.'}), 404

    # Fetch user's address from the database
    address_info = get_user_address(user_id)
    if not address_info:
        return jsonify({'message': 'Address not found for user.'}), 404
    address = address_info[0]

    # Fetch saved card information for the user from the database
    card_info = get_saved_card_info(user_id)
    if not card_info:
        return jsonify({'message': 'No saved card information found for user.'}), 404

    card_number, expiration_date, cvv = card_info

    # Calculate total amount including shipping fee
    total = sum(item[3] for item in cart_items) + 20  # Price is at index 3

    # Process payment
    if process_payment(card_info):
        # Record transaction in the database
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, total, status) VALUES (?, ?, ?)",
                  (user_id, total, 'success'))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Payment successful. Transaction recorded.'}), 200
    else:
        return jsonify({'message': 'Payment failed.'}), 400

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)