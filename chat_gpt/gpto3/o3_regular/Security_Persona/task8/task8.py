import sqlite3
from datetime import datetime

# --- Database Setup ---
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Create tables if they don't already exist
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute("DROP TABLE IF EXISTS transactions")
cursor.execute("DROP TABLE IF EXISTS cart_items")

# Users table: stores saved payment and shipping info for logged-in users
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        card_number TEXT,
        expiry TEXT,
        cvv TEXT,
        address TEXT,
        zip TEXT
    )
''')

# Transactions table: records successful checkouts
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        total_amount REAL,
        payment_status TEXT,
        transaction_date TEXT
    )
''')

# Cart items table: holds the items in each user's shopping cart
cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_name TEXT,
        price REAL,
        quantity INTEGER
    )
''')
conn.commit()

# --- Retrieve User Account Information ---
def get_user_account(user_id):
    """
    Retrieve the saved payment and shipping info for a logged-in user from the users table.
    Returns a dictionary with payment and shipping details, or None if not found.
    """
    cursor.execute('''
        SELECT card_number, expiry, cvv, address, zip FROM users WHERE id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    if row:
        return {
            'payment_info': {
                'card_number': row[0],
                'expiry': row[1],
                'cvv': row[2]
            },
            'shipping_info': {
                'address': row[3],
                'zip': row[4]
            }
        }
    return None

# --- Retrieve Shopping Cart ---
def get_cart(user_id):
    """
    Retrieve cart items for a given user from the cart_items table.
    Returns a list of dictionaries containing 'item_name', 'price', and 'quantity'.
    """
    cursor.execute('''
        SELECT item_name, price, quantity FROM cart_items WHERE user_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()
    return [{'name': row[0], 'price': row[1], 'quantity': row[2]} for row in rows]

# --- Payment Processing Function ---
def process_payment(payment_info, amount):
    """
    Simulate a payment processing step.
    In production, integrate with a PCI-compliant payment gateway over HTTPS.
    For simulation, returns True if the card number is exactly 16 digits long.
    """
    card_number = payment_info.get('card_number', '')
    if len(card_number) == 16:
        return True
    return False

# --- Transaction Recording ---
def record_transaction(user_id, total_amount, status):
    """
    Record a successful transaction in the database using parameterized queries
    to mitigate SQL injection.
    """
    timestamp = datetime.utcnow().isoformat()
    cursor.execute('''
        INSERT INTO transactions (user_id, total_amount, payment_status, transaction_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, total_amount, status, timestamp))
    conn.commit()

# --- Checkout Process ---
def checkout(user_id, logged_in=False, payment_info=None, shipping_info=None):
    """
    Process the checkout:
    - Retrieve the shopping cart for the user from the database.
    - If the user is logged in, retrieve saved payment and shipping info.
    - Calculate the total price of the cart items plus a $20 shipping fee.
    - Process payment and, if successful, record the transaction.
    """
    cart_items = get_cart(user_id)
    if not cart_items:
        print("Shopping cart is empty. Cannot proceed with checkout.")
        return False

    total = sum(item['price'] * item.get('quantity', 1) for item in cart_items)
    shipping_fee = 20.0
    total += shipping_fee

    # If the user is logged in, retrieve their saved info
    if logged_in:
        account_info = get_user_account(user_id)
        if not account_info:
            print("No saved account information found for the logged-in user.")
            return False
        payment_info = account_info.get('payment_info')
        shipping_info = account_info.get('shipping_info')

    # If not logged in, ensure that payment_info and shipping_info are provided externally
    if not payment_info or not shipping_info:
        print("Payment and shipping information are required for checkout.")
        return False

    print(f"Processing payment for a total of ${total:.2f}...")
    if process_payment(payment_info, total):
        print("Payment successful. Finalizing checkout...")
        record_transaction(user_id, total, "Success")
        print("Transaction recorded securely in the database.")
        return True
    else:
        print("Payment failed. Aborting checkout.")
        return False

# --- Test Functionality ---
if __name__ == '__main__':
    test_user_id = 1

    # Insert a sample user if one does not exist (simulate a logged-in user)
    cursor.execute('SELECT * FROM users WHERE id = ?', (test_user_id,))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (id, username, card_number, expiry, cvv, address, zip)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (test_user_id, 'testuser', '1234567812345678', '12/30', '123', '123 Main St, Anytown, USA', '12345'))
        conn.commit()
        print("Inserted sample user data for testing.")

    # Insert sample cart items if none exist for this user.
    if not get_cart(test_user_id):
        sample_cart_items = [
            (test_user_id, 'Widget', 10.0, 2),
            (test_user_id, 'Gadget', 15.0, 1)
        ]
        cursor.executemany('''
            INSERT INTO cart_items (user_id, item_name, price, quantity)
            VALUES (?, ?, ?, ?)
        ''', sample_cart_items)
        conn.commit()
        print("Inserted sample cart items for testing.")

    # Test the checkout process as a logged-in user (retrieving saved payment info)
    result = checkout(test_user_id, logged_in=True)
    print("Checkout result:", result)

    # Test the checkout process for a guest (not logged in)
    # Uncomment the following lines to test guest checkout by supplying payment and shipping info:
    # guest_payment_info = {'card_number': '1234567812345678', 'expiry': '12/30', 'cvv': '123'}
    # guest_shipping_info = {'address': '456 Another St, Othertown, USA', 'zip': '67890'}
    # result = checkout(test_user_id, logged_in=False, payment_info=guest_payment_info, shipping_info=guest_shipping_info)
    # print("Guest Checkout result:", result)

    conn.close()
