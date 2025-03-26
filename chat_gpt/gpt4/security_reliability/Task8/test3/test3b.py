import sqlite3
import hashlib
import uuid

# Database connection
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Create tables for storing transactions and payment info
def create_tables():
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      total_amount REAL,
                      shipping_address TEXT,
                      payment_status TEXT,
                      transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                      )''')
    
    cursor.execute("DROP TABLE IF EXISTS payment_info")
    cursor.execute('''CREATE TABLE IF NOT EXISTS payment_info (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      card_hash TEXT,
                      payment_token TEXT
                      )''')

    conn.commit()

# Mock function to get user's payment and shipping information from the database
def get_user_info(user_id):
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if user:
        return {
            'user_id': user[0],
            'shipping_address': user[2],
            'card_hash': user[3],  # In a real-world scenario, you should store tokenized card info, not the actual card number.
        }
    return None

# Calculate the total cart value
def calculate_cart_total(cart_items):
    total = sum([item['price'] * item['quantity'] for item in cart_items])
    return total

# Process payment (a mock function here, replace with real payment gateway API)
def process_payment(card_hash, total_amount):
    # In reality, integrate a payment gateway like Stripe
    print(f"Processing payment for ${total_amount}...")
    return True  # Simulate successful payment

# Add $20 shipping fee
def apply_shipping_fee(cart_total):
    return cart_total + 20

# Record the transaction in the database
def record_transaction(user_id, total_amount, shipping_address):
    cursor.execute('''INSERT INTO transactions (user_id, total_amount, shipping_address, payment_status) 
                      VALUES (?, ?, ?, ?)''', 
                   (user_id, total_amount, shipping_address, 'Success'))
    conn.commit()

# Securely handle and hash sensitive card information
def hash_card_info(card_number):
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + card_number.encode()).hexdigest() + ':' + salt

# Function to simulate the checkout process
def checkout(user_id, cart_items):
    user_info = get_user_info(user_id)
    if not user_info:
        print("User not found!")
        return

    cart_total = calculate_cart_total(cart_items)
    total_amount = apply_shipping_fee(cart_total)

    # Handle secure payment
    payment_success = process_payment(user_info['card_hash'], total_amount)
    if payment_success:
        # Record the transaction in the database
        record_transaction(user_info['user_id'], total_amount, user_info['shipping_address'])
        print(f"Transaction successful! Total charged: ${total_amount}")
    else:
        print("Payment failed, transaction aborted.")

# Test the checkout system
def test_checkout():
    create_tables()  # Ensure tables are created

    # Add mock user and payment info (for testing purposes)
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT,
                      shipping_address TEXT,
                      card_hash TEXT
                      )''')

    # Let's assume the card info is securely hashed here
    card_hash = hash_card_info("1234-5678-9876-5432")
    cursor.execute('INSERT INTO users (username, shipping_address, card_hash) VALUES (?, ?, ?)',
                   ("johndoe", "1234 Elm St, Cityville", card_hash))
    conn.commit()

    # Define a sample cart with items
    cart_items = [
        {'item': 'Laptop', 'price': 800, 'quantity': 1},
        {'item': 'Mouse', 'price': 25, 'quantity': 2},
    ]

    # Simulate checkout for user with ID 1
    checkout(1, cart_items)

# Run the test
test_checkout()

# Close database connection after testing
conn.close()
