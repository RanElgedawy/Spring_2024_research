import sqlite3
from hashlib import sha256

# Secure handling of card info would normally involve tokenization or encryption
# Simulated payment processing function (you would replace with a real API in production)
def process_payment(card_info, amount):
    # Simulating a payment success
    return True if card_info and amount > 0 else False

# Create or connect to the SQLite database
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Create necessary tables for transactions and orders (if they don't already exist)
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT,
    shipping_address TEXT,
    payment_info TEXT -- Simulating stored encrypted card info
)
''')

cursor.execute("DROP TABLE IF EXISTS carts")
cursor.execute('''
CREATE TABLE IF NOT EXISTS carts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    item_name TEXT,
    price REAL,
    quantity INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

cursor.execute("DROP TABLE IF EXISTS transactions")
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    total_amount REAL,
    shipping_fee REAL,
    payment_status TEXT,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# Helper function to calculate the total cart value
def calculate_cart_total(user_id):
    cursor.execute('SELECT SUM(price * quantity) FROM carts WHERE user_id = ?', (user_id,))
    total = cursor.fetchone()[0] or 0
    return total

# Checkout function
def checkout(user_id):
    # Fetch user information
    cursor.execute('SELECT shipping_address, payment_info FROM users WHERE id = ?', (user_id,))
    user_info = cursor.fetchone()
    
    if not user_info:
        return "Error: User not found."

    shipping_address, encrypted_payment_info = user_info
    
    # Decrypt or securely handle the stored card info (for simulation, we assume it's ready to use)
    card_info = sha256(encrypted_payment_info.encode()).hexdigest()  # Not real encryption

    # Calculate total cart value
    cart_total = calculate_cart_total(user_id)
    if cart_total == 0:
        return "Error: Cart is empty."
    
    shipping_fee = 20.0
    total_amount = cart_total + shipping_fee
    
    # Process the payment
    payment_success = process_payment(card_info, total_amount)
    
    if not payment_success:
        return "Error: Payment failed."

    # Record the transaction
    cursor.execute('''
    INSERT INTO transactions (user_id, total_amount, shipping_fee, payment_status)
    VALUES (?, ?, ?, ?)
    ''', (user_id, total_amount, shipping_fee, 'Success'))
    
    conn.commit()
    
    return f"Checkout successful! Total charged: ${total_amount}"

# Test data setup (add users and cart items)
def setup_test_data():
    # Insert a test user
    cursor.execute('''
    INSERT OR IGNORE INTO users (id, username, email, shipping_address, payment_info)
    VALUES (1, 'testuser', 'testuser@example.com', '123 Test St', 'secure_card_info')
    ''')

    # Insert some items in the cart for the test user
    cursor.execute('''
    INSERT OR REPLACE INTO carts (user_id, item_name, price, quantity)
    VALUES
    (1, 'Laptop', 999.99, 1),
    (1, 'Mouse', 49.99, 2)
    ''')

    conn.commit()

# Function to test the checkout functionality
def test_checkout():
    setup_test_data()  # Setup test data
    result = checkout(1)  # Test checkout for user with ID 1
    print(result)

# Run the test checkout
test_checkout()

# Close the database connection
conn.close()
