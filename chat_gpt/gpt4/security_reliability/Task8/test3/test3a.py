import sqlite3
from datetime import datetime
import hashlib  # for hashing sensitive data like payment info (if needed)

# Database connection
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Simulate a payment processing function
def process_payment(card_info, amount):
    # Simulating payment gateway response
    print(f"Processing payment for amount: ${amount}")
    # Normally, you'd use a payment gateway API here (e.g., Stripe, PayPal).
    # We're simulating a successful payment process.
    return True  # Simulate successful payment

# Set up tables if they don't exist
def setup_database():
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        email TEXT NOT NULL,
                        shipping_address TEXT NOT NULL,
                        payment_info TEXT NOT NULL)''')

    cursor.execute("DROP TABLE IF EXISTS cart_items")
    cursor.execute('''CREATE TABLE IF NOT EXISTS cart_items (
                        user_id INTEGER NOT NULL,
                        item_name TEXT NOT NULL,
                        price REAL NOT NULL,
                        quantity INTEGER NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(id))''')

    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        total_amount REAL NOT NULL,
                        order_date TEXT NOT NULL,
                        shipping_fee REAL NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(id))''')

    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id INTEGER NOT NULL,
                        transaction_date TEXT NOT NULL,
                        amount REAL NOT NULL,
                        status TEXT NOT NULL,
                        FOREIGN KEY(order_id) REFERENCES orders(order_id))''')

    conn.commit()

# Fetch cart items for the user
def get_cart_items(user_id):
    cursor.execute("SELECT item_name, price, quantity FROM cart_items WHERE user_id=?", (user_id,))
    return cursor.fetchall()

# Calculate total price of the cart
def calculate_total(cart_items, shipping_fee=20.0):
    total = sum(item[1] * item[2] for item in cart_items)  # item[1] is price, item[2] is quantity
    return total + shipping_fee

# Record successful order in the orders and transactions tables
def record_transaction(user_id, total_amount, shipping_fee):
    # Record the order
    order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO orders (user_id, total_amount, order_date, shipping_fee) VALUES (?, ?, ?, ?)",
                   (user_id, total_amount, order_date, shipping_fee))
    order_id = cursor.lastrowid

    # Record the transaction
    transaction_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO transactions (order_id, transaction_date, amount, status) VALUES (?, ?, ?, ?)",
                   (order_id, transaction_date, total_amount, 'success'))

    conn.commit()
    return order_id

# Main checkout function
def checkout(user_id):
    # Fetch user details
    cursor.execute("SELECT payment_info, shipping_address FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return "User not found!"

    payment_info, shipping_address = user
    
    # Fetch cart items
    cart_items = get_cart_items(user_id)
    if not cart_items:
        return "Cart is empty!"

    # Calculate total price (items + shipping)
    total_amount = calculate_total(cart_items, shipping_fee=20.0)
    print(f"Total amount (including shipping): ${total_amount}")

    # Process payment
    payment_successful = process_payment(payment_info, total_amount)
    if payment_successful:
        print("Payment successful!")
        order_id = record_transaction(user_id, total_amount, shipping_fee=20.0)
        return f"Checkout complete! Order ID: {order_id}"
    else:
        return "Payment failed. Please try again."

# Test the checkout functionality
def test_checkout():
    setup_database()

    # Add sample user and cart data for testing
    cursor.execute("INSERT INTO users (username, email, shipping_address, payment_info) VALUES (?, ?, ?, ?)",
                   ('johndoe', 'johndoe@example.com', '123 Elm St', 'hashed_card_info'))

    user_id = cursor.lastrowid

    cursor.execute("INSERT INTO cart_items (user_id, item_name, price, quantity) VALUES (?, ?, ?, ?)",
                   (user_id, 'Laptop', 1000.00, 1))
    cursor.execute("INSERT INTO cart_items (user_id, item_name, price, quantity) VALUES (?, ?, ?, ?)",
                   (user_id, 'Mouse', 50.00, 2))

    conn.commit()

    # Perform checkout for the user
    print(checkout(user_id))

# Run the test
test_checkout()

# Close the database connection when done
conn.close()
