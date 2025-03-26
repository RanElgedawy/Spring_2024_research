import sqlite3
from flask import Flask, request, jsonify
import hashlib

app = Flask(__name__)

# Create a connection to the SQLite database
def create_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    return conn

# Securely hash the card details (in production use, don't handle card details directly)
def hash_card_details(card_number):
    return hashlib.sha256(card_number.encode()).hexdigest()

# Create necessary tables
def initialize_database():
    conn = create_db_connection()
    cursor = conn.cursor()

    # Create a table to store transactions if it doesn't already exist
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total_amount REAL,
            payment_successful BOOLEAN,
            shipping_address TEXT,
            card_hash TEXT
        )
    ''')
    
    # Example table for storing user info (already assumed to exist in your case)
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            shipping_address TEXT,
            payment_info TEXT  -- In production, store a token, not raw card info
        )
    ''')
    
    # Example table for cart items (already assumed to exist in your case)
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            user_id INTEGER,
            item_id INTEGER,
            quantity INTEGER,
            price REAL
        )
    ''')

    conn.commit()
    conn.close()

# Get user's cart items
def get_cart_items(user_id):
    conn = create_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT item_id, quantity, price FROM cart WHERE user_id = ?
    ''', (user_id,))
    items = cursor.fetchall()

    conn.close()
    return items

# Calculate the total amount for the user's cart, including a $20 shipping fee
def calculate_total(items):
    total = sum(item[1] * item[2] for item in items)  # quantity * price for each item
    total += 20  # Add shipping fee
    return total

# Simulate a payment processing function
def process_payment(card_info, total_amount):
    # In a real-world scenario, integrate with a payment gateway API (e.g., Stripe)
    # For the sake of this example, let's assume the payment always succeeds.
    return True

# Save a transaction in the database
def record_transaction(user_id, total_amount, payment_successful, shipping_address, card_hash):
    conn = create_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO transactions (user_id, total_amount, payment_successful, shipping_address, card_hash)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, total_amount, payment_successful, shipping_address, card_hash))

    conn.commit()
    conn.close()

# Checkout route
@app.route('/checkout', methods=['POST'])
def checkout():
    user_id = request.json.get('user_id')  # Assume user is logged in and we have their ID
    card_info = request.json.get('card_info')

    # Fetch the user's shipping address and payment info (in real life, tokenized)
    conn = create_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT shipping_address FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    shipping_address = user_data[0]

    # Get items from cart
    items = get_cart_items(user_id)

    if not items:
        return jsonify({'message': 'Cart is empty.'}), 400

    # Calculate total amount with shipping fee
    total_amount = calculate_total(items)

    # Process payment
    payment_successful = process_payment(card_info, total_amount)

    # Hash card details for secure storage (if required, not recommended)
    card_hash = hash_card_details(card_info)

    if payment_successful:
        # Record the transaction in the database
        record_transaction(user_id, total_amount, payment_successful, shipping_address, card_hash)
        return jsonify({'message': 'Payment successful and transaction recorded.'}), 200
    else:
        return jsonify({'message': 'Payment failed.'}), 402

# Initialize the database
initialize_database()

if __name__ == '__main__':
    app.run(debug=True)
