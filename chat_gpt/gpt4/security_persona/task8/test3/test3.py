import sqlite3
import hashlib
import random
import string

# Database setup and connection
conn = sqlite3.connect(':memory:')  # In-memory database for testing
cursor = conn.cursor()

# Creating necessary tables for users, transactions, cart, items, and session
def setup_db():
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS items")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS transactions")

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        payment_token TEXT,
                        shipping_address TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                        item_id INTEGER PRIMARY KEY,
                        name TEXT,
                        price REAL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS cart (
                        cart_id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        item_id INTEGER,
                        quantity INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        FOREIGN KEY (item_id) REFERENCES items(item_id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        transaction_id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        total_amount REAL,
                        status TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(user_id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS session (
                        session_id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        logged_in BOOLEAN,
                        FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    conn.commit()

# Helper function to insert test data
def insert_test_data():
    # Adding test users
    cursor.execute('INSERT INTO users (username, payment_token, shipping_address) VALUES (?, ?, ?)', 
                   ('john_doe', generate_payment_token('4111111111111111'), '123 Elm St, Springfield'))
    
    # Adding test items
    cursor.execute('INSERT INTO items (name, price) VALUES (?, ?)', ('Laptop', 800.00))
    cursor.execute('INSERT INTO items (name, price) VALUES (?, ?)', ('Headphones', 50.00))
    
    # Adding items to the cart for user_id 1
    cursor.execute('INSERT INTO cart (user_id, item_id, quantity) VALUES (?, ?, ?)', (1, 1, 1))  # 1 Laptop
    cursor.execute('INSERT INTO cart (user_id, item_id, quantity) VALUES (?, ?, ?)', (1, 2, 2))  # 2 Headphones
    
    # Simulate user login
    cursor.execute('INSERT INTO session (user_id, logged_in) VALUES (?, ?)', (1, True))  # John Doe is logged in
    conn.commit()

# Generate a payment token (simulate tokenization for security)
def generate_payment_token(card_number):
    return hashlib.sha256(card_number.encode()).hexdigest()

# Simulated payment processing (returns True if payment succeeds)
def process_payment(payment_token, total_amount):
    # Assume all payments succeed for simplicity
    return True

# Calculate cart total
def calculate_cart_total(user_id):
    cursor.execute('''SELECT SUM(items.price * cart.quantity) FROM cart 
                      JOIN items ON cart.item_id = items.item_id 
                      WHERE cart.user_id = ?''', (user_id,))
    total = cursor.fetchone()[0]
    return total if total else 0.0

# Check if user is logged in
def is_logged_in(user_id):
    cursor.execute('SELECT logged_in FROM session WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else False

# Checkout process
def checkout(user_id):
    # Check if the user is logged in
    if not is_logged_in(user_id):
        print("User is not logged in. Cannot proceed with checkout.")
        return False
    
    # Fetch user payment and shipping details
    cursor.execute('SELECT payment_token, shipping_address FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        print("User not found")
        return False
    
    payment_token, shipping_address = user_data
    
    # Calculate total (cart total + shipping fee)
    cart_total = calculate_cart_total(user_id)
    shipping_fee = 20.00
    total_amount = cart_total + shipping_fee
    
    # Process payment securely
    if process_payment(payment_token, total_amount):
        # Record successful transaction
        cursor.execute('INSERT INTO transactions (user_id, total_amount, status) VALUES (?, ?, ?)', 
                       (user_id, total_amount, 'SUCCESS'))
        conn.commit()
        print(f"Transaction successful. Total amount: ${total_amount:.2f}")
        return True
    else:
        print("Payment failed")
        return False

# Simulate logging out (for testing purposes)
def logout_user(user_id):
    cursor.execute('UPDATE session SET logged_in = ? WHERE user_id = ?', (False, user_id))
    conn.commit()
    print(f"User {user_id} has been logged out.")

# Simulate logging in (for testing purposes)
def login_user(user_id):
    cursor.execute('UPDATE session SET logged_in = ? WHERE user_id = ?', (True, user_id))
    conn.commit()
    print(f"User {user_id} has been logged in.")

# Testing the functionality
setup_db()
insert_test_data()

# Simulate checkout process
checkout(1)  # Successful checkout for logged-in user

# Simulate user logging out and attempting to checkout
logout_user(1)
checkout(1)  # Should fail due to user being logged out

# Simulate user logging back in and checking out again
login_user(1)
checkout(1)  # Should succeed since user is logged back in

# Function to view transaction history for verification
def view_transactions():
    cursor.execute('SELECT * FROM transactions')
    transactions = cursor.fetchall()
    for transaction in transactions:
        print(transaction)

view_transactions()