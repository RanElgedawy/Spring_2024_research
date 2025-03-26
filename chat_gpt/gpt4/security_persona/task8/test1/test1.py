import sqlite3
from hashlib import sha256
from datetime import datetime

# Simulate an in-memory session store (in a real-world app, use session management like Flask's session or JWT)
logged_in_users = {}

# Database setup
def setup_database():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS orders")


    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        payment_info TEXT NOT NULL,
        shipping_address TEXT NOT NULL
    )
    ''')

    # Create cart table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        item_price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Create orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        items TEXT NOT NULL,
        shipping_fee REAL NOT NULL,
        payment_status TEXT NOT NULL,
        order_date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    conn.commit()
    conn.close()

# Placeholder function for processing payment
def process_payment(payment_info, amount):
    """
    In a real-world scenario, this function would use a third-party API to process the payment.
    The function will return True if the payment is successful, otherwise False.
    """
    return True if payment_info else False

# Calculate the total order amount including shipping fee
def calculate_total(cart_items, shipping_fee):
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return total + shipping_fee

# Function to get the cart items from the database
def get_cart_items(user_id):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    cursor.execute('SELECT item_name, item_price, quantity FROM cart WHERE user_id = ?', (user_id,))
    items = cursor.fetchall()
    
    cart_items = [{'name': item[0], 'price': item[1], 'quantity': item[2]} for item in items]
    
    conn.close()
    
    return cart_items

# Check if the user is logged in
def is_user_logged_in(username):
    return logged_in_users.get(username) is not None

# User login function
def login(username, password):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Hash the input password
    hashed_password = sha256(password.encode()).hexdigest()

    # Check if the user exists with the given username and password
    cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, hashed_password))
    user = cursor.fetchone()

    if user:
        # Simulate a session by adding the user to the logged_in_users dictionary
        logged_in_users[username] = user[0]
        conn.close()
        return f"User {username} logged in successfully."
    else:
        conn.close()
        return "Invalid username or password."

# User logout function
def logout(username):
    if logged_in_users.get(username):
        del logged_in_users[username]
        return f"User {username} logged out."
    return "User not logged in."

# Checkout function with login check
def checkout(username):
    if not is_user_logged_in(username):
        return "User is not logged in. Please log in first."

    # Get the user's ID from the session
    user_id = logged_in_users[username]

    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Fetch user data (e.g., payment information, shipping address)
    cursor.execute('SELECT payment_info, shipping_address FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return "User not found."

    payment_info, shipping_address = user
    shipping_fee = 20.0

    # Get the cart items from the database
    cart_items = get_cart_items(user_id)

    if not cart_items:
        conn.close()
        return "Your cart is empty."

    # Calculate total amount
    total_amount = calculate_total(cart_items, shipping_fee)

    # Process payment
    if process_payment(payment_info, total_amount):
        # Payment successful, record the transaction
        items_str = ', '.join([f"{item['name']} (x{item['quantity']})" for item in cart_items])
        cursor.execute('''
        INSERT INTO orders (user_id, total_amount, items, shipping_fee, payment_status, order_date)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, total_amount, items_str, shipping_fee, 'success', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        # Clear the cart after successful purchase
        cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))

        conn.commit()
        conn.close()
        return "Checkout successful. Order placed."
    else:
        conn.close()
        return "Payment failed. Please try again."

# Function to test checkout flow with login
def test_checkout_flow():
    # Setup database
    setup_database()

    # Add a test user (in a real system, user registration would handle this)
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    hashed_password = sha256("password123".encode()).hexdigest()

    cursor.execute('''
    INSERT INTO users (username, password, payment_info, shipping_address)
    VALUES (?, ?, ?, ?)
    ''', ('testuser', hashed_password, 'fake_card_info', '123 Test St, Test City'))

    conn.commit()

    # Get the user's ID
    user_id = cursor.lastrowid

    # Add items to the cart for the user
    cart_items = [
        {'name': 'Item1', 'price': 50.0, 'quantity': 2},
        {'name': 'Item2', 'price': 30.0, 'quantity': 1}
    ]
    
    for item in cart_items:
        cursor.execute('''
        INSERT INTO cart (user_id, item_name, item_price, quantity)
        VALUES (?, ?, ?, ?)
        ''', (user_id, item['name'], item['price'], item['quantity']))
    
    conn.commit()
    conn.close()

    # Test login and checkout flow
    print(login('testuser', 'password123'))  # User logs in
    print(checkout('testuser'))  # Proceed with checkout
    print(logout('testuser'))  # User logs out

# Run the test
if __name__ == "__main__":
    test_checkout_flow()