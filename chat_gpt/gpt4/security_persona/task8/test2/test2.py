import sqlite3
import hashlib
import random
import string

# Simulate a session dictionary to store the logged-in user's state
session = {"user_id": None}

# Initialize the SQLite database
def init_db():
    # Create a connection to the SQLite database
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS cart_items")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        payment_info TEXT NOT NULL,
        shipping_info TEXT NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        total REAL,
        status TEXT NOT NULL,
        payment_reference TEXT NOT NULL,
        shipping_address TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart (
        cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cart_id INTEGER,
        item_name TEXT NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (cart_id) REFERENCES cart(cart_id)
    )''')

    conn.commit()
    conn.close()

# Fetch user's cart items from the database
def get_user_cart(user_id):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Retrieve cart_id for the user
    cursor.execute("SELECT cart_id FROM cart WHERE user_id=?", (user_id,))
    cart = cursor.fetchone()

    if not cart:
        print("No cart found for this user.")
        return []

    cart_id = cart[0]

    # Retrieve all items from the cart_items table
    cursor.execute("SELECT item_name, price FROM cart_items WHERE cart_id=?", (cart_id,))
    cart_items = cursor.fetchall()

    conn.close()

    if cart_items:
        return [{"item_name": item[0], "price": item[1]} for item in cart_items]
    else:
        print("Cart is empty.")
        return []

# Simulate payment processing (fake for demo purposes)
def process_payment(payment_info, total):
    # Simulate payment validation and return a mock payment reference number if successful
    if payment_info and total > 0:
        payment_reference = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        return True, payment_reference
    return False, None

# Securely handle checkout process
def checkout():
    # Ensure the user is logged in before proceeding
    if not session["user_id"]:
        print("User not logged in. Please log in to proceed.")
        return False

    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Fetch user payment and shipping info securely from database
    cursor.execute("SELECT payment_info, shipping_info FROM users WHERE user_id=?", (session["user_id"],))
    user_info = cursor.fetchone()

    if not user_info:
        print("User not found.")
        return False

    payment_info, shipping_info = user_info

    # Get the user's cart items from the database
    cart_items = get_user_cart(session["user_id"])
    if not cart_items:
        print("Cannot proceed with checkout, cart is empty.")
        return False

    cart_total = sum(item['price'] for item in cart_items)

    # Add a $20 shipping fee
    shipping_fee = 20.0
    total_with_shipping = cart_total + shipping_fee

    # Process payment securely (simulated for demo)
    payment_success, payment_reference = process_payment(payment_info, total_with_shipping)

    if payment_success:
        # Record the transaction in the transactions table
        cursor.execute('''
        INSERT INTO transactions (user_id, total, status, payment_reference, shipping_address)
        VALUES (?, ?, ?, ?, ?)
        ''', (session["user_id"], total_with_shipping, 'Success', payment_reference, shipping_info))
        conn.commit()
        print("Transaction successful!")
        print(f"Total charged: ${total_with_shipping}")
        print(f"Payment reference: {payment_reference}")
        return True
    else:
        print("Payment failed. Transaction not recorded.")
        return False

# Function to simulate a user login and store the session
def login(username, password):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Hash the password to simulate secure login (use a better hash method in production)
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute("SELECT user_id FROM users WHERE username=? AND password_hash=?", (username, password_hash))
    user = cursor.fetchone()

    if user:
        session["user_id"] = user[0]  # Store user_id in session to indicate login
        print(f"User {username} logged in successfully.")
        return True
    else:
        print("Invalid login.")
        return False

# Add a test user and cart to the database (for testing)
def add_test_user_and_cart():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    username = "testuser"
    password = "password123"
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    payment_info = "VISA 1234-XXXX-XXXX-5678"  # Never store full card numbers like this
    shipping_info = "123 Test St, Test City, TX"

    # Add user
    cursor.execute('''
    INSERT INTO users (username, password_hash, payment_info, shipping_info)
    VALUES (?, ?, ?, ?)
    ''', (username, password_hash, payment_info, shipping_info))

    user_id = cursor.lastrowid

    # Add a cart for the user
    cursor.execute('''
    INSERT INTO cart (user_id)
    VALUES (?)
    ''', (user_id,))
    
    cart_id = cursor.lastrowid

    # Add items to the cart
    cart_items = [
        {"item_name": "Laptop", "price": 1200},
        {"item_name": "Headphones", "price": 200}
    ]

    for item in cart_items:
        cursor.execute('''
        INSERT INTO cart_items (cart_id, item_name, price)
        VALUES (?, ?, ?)
        ''', (cart_id, item['item_name'], item['price']))

    conn.commit()
    conn.close()

# Main function to initialize the DB and perform a test checkout
def main():
    init_db()
    add_test_user_and_cart()  # Add a test user and their cart for testing

    # Simulate user login
    username = "testuser"
    password = "password123"
    if login(username, password):
        # Proceed with checkout if login is successful
        checkout()

if __name__ == "__main__":
    main()