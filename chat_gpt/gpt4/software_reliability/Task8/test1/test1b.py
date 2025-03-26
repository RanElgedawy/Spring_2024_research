import sqlite3
from random import randint

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Automatically create orders and transactions tables
def create_tables():
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS transactions")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        shipping_address TEXT NOT NULL,
        total_amount REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        payment_status TEXT NOT NULL,
        payment_amount REAL NOT NULL,
        payment_method TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    )
    ''')
    
    conn.commit()

# Mock function to simulate retrieving user info
def get_user_profile(user_id):
    # Simulating the user data retrieval from the user table
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

# Mock function to retrieve items from the user's cart
def get_cart_items(user_id):
    # Fetch cart items for the given user
    cursor.execute('''
    SELECT p.product_id, p.name, p.price, c.quantity
    FROM carts c
    JOIN products p ON p.product_id = c.product_id
    WHERE c.user_id = ?
    ''', (user_id,))
    
    return cursor.fetchall()

# Function to calculate the total amount
def calculate_total(cart_items, shipping_fee=20):
    total = sum(item[2] * item[3] for item in cart_items)  # item[2] = price, item[3] = quantity
    total += shipping_fee  # Add shipping fee
    return total

# Mock function to simulate payment processing
def process_payment(user_id, total_amount, payment_method="credit_card"):
    # Mocking a successful payment, normally you'd integrate with a payment gateway
    payment_success = randint(0, 1)  # Randomly mock success or failure
    return payment_success == 1

# Function to record an order in the database
def submit_order(user_id, shipping_address, total_amount):
    cursor.execute('''
    INSERT INTO orders (user_id, shipping_address, total_amount)
    VALUES (?, ?, ?)
    ''', (user_id, shipping_address, total_amount))
    
    conn.commit()
    return cursor.lastrowid

# Function to record transaction in the database
def record_transaction(order_id, payment_status, payment_amount, payment_method):
    cursor.execute('''
    INSERT INTO transactions (order_id, payment_status, payment_amount, payment_method)
    VALUES (?, ?, ?, ?)
    ''', (order_id, payment_status, payment_amount, payment_method))
    
    conn.commit()

# Checkout function to handle the entire process
def checkout(user_id):
    # Retrieve the user profile
    user_profile = get_user_profile(user_id)
    
    if not user_profile:
        print("User not found.")
        return

    # Get the cart items
    cart_items = get_cart_items(user_id)
    
    if not cart_items:
        print("Cart is empty.")
        return
    
    # Calculate the total amount with the shipping fee
    total_amount = calculate_total(cart_items)
    
    # Retrieve the shipping address (from user profile)
    shipping_address = user_profile[3]  # Assuming the 4th column is the shipping address
    
    # Process the payment
    payment_method = "credit_card"
    payment_success = process_payment(user_id, total_amount, payment_method)
    
    if payment_success:
        print("Payment successful. Proceeding with order submission.")
        # Submit the order and get the order ID
        order_id = submit_order(user_id, shipping_address, total_amount)
        
        # Record the successful transaction
        record_transaction(order_id, "Success", total_amount, payment_method)
        
        print(f"Order {order_id} submitted successfully!")
    else:
        print("Payment failed. Transaction aborted.")
        # Record failed transaction
        record_transaction(None, "Failed", total_amount, payment_method)

# Test the functionality
if __name__ == "__main__":
    create_tables()
    
    # Mock user ID for testing purposes
    user_id = 1
    
    # Checkout process
    checkout(user_id)

    # Close the database connection
    conn.close()
