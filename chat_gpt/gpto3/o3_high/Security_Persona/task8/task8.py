import sqlite3
import json
import datetime

def create_transaction_table(conn):
    """
    Create the transactions table if it doesn't already exist.
    """
    with conn:
        conn.execute("DROP TABLE IF EXISTS transactions")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                items TEXT,
                total REAL,
                shipping_address TEXT,
                transaction_date TEXT
            )
        ''')

def create_order_table(conn):
    """
    Create the orders table that records order submissions with their status.
    """
    with conn:
        conn.execute("DROP TABLE IF EXISTS orders")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER,
                user_id TEXT,
                order_status TEXT,
                submission_date TEXT,
                FOREIGN KEY(transaction_id) REFERENCES transactions(id)
            )
        ''')

def create_cart_table(conn):
    """
    Create the cart table to store shopping cart items for users.
    """
    with conn:
        conn.execute("DROP TABLE IF EXISTS cart")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                name TEXT,
                price REAL,
                quantity INTEGER
            )
        ''')

def create_user_address_table(conn):
    """
    Create a table to store user shipping address information.
    """
    with conn:
        conn.execute("DROP TABLE IF EXISTS user_addresses")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_addresses (
                user_id TEXT PRIMARY KEY,
                address TEXT
            )
        ''')

def create_user_card_table(conn):
    """
    Create a table to store a user's saved card information.
    Note: In production, sensitive card data should be tokenized or stored in a secure vault.
    """
    with conn:
        conn.execute("DROP TABLE IF EXISTS user_cards")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_cards (
                user_id TEXT PRIMARY KEY,
                card_number TEXT,
                expiry TEXT,
                cvv TEXT
            )
        ''')

def add_item_to_cart(conn, user_id, name, price, quantity):
    """
    Add an item to the user's shopping cart.
    """
    with conn:
        conn.execute('''
            INSERT INTO cart (user_id, name, price, quantity)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, price, quantity))

def get_cart_items(conn, user_id):
    """
    Retrieve shopping cart items for a given user from the database.
    Returns a list of dictionaries with keys: name, price, quantity.
    """
    cursor = conn.execute('''
        SELECT name, price, quantity
        FROM cart
        WHERE user_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()
    return [{'name': row[0], 'price': row[1], 'quantity': row[2]} for row in rows]

def clear_cart(conn, user_id):
    """
    Clear the shopping cart for a given user.
    """
    with conn:
        conn.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    print("Cart cleared.")

def add_user_address(conn, user_id, address):
    """
    Insert or update a user's shipping address in the database.
    """
    with conn:
        conn.execute('''
            INSERT OR REPLACE INTO user_addresses (user_id, address)
            VALUES (?, ?)
        ''', (user_id, address))

def get_user_address(conn, user_id):
    """
    Retrieve the user's shipping address from the database.
    Returns the address as a string or None if not found.
    """
    cursor = conn.execute('''
        SELECT address
        FROM user_addresses
        WHERE user_id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    return row[0] if row else None

def add_user_card(conn, user_id, card_number, expiry, cvv):
    """
    Insert or update a user's saved card information in the database.
    Note: Do not store raw card data in production; use a secure method.
    """
    with conn:
        conn.execute('''
            INSERT OR REPLACE INTO user_cards (user_id, card_number, expiry, cvv)
            VALUES (?, ?, ?, ?)
        ''', (user_id, card_number, expiry, cvv))

def get_user_card(conn, user_id):
    """
    Retrieve the user's saved card information from the database.
    Returns a dictionary with card info or None if not found.
    """
    cursor = conn.execute('''
        SELECT card_number, expiry, cvv
        FROM user_cards
        WHERE user_id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    if row:
        return {'number': row[0], 'expiry': row[1], 'cvv': row[2]}
    return None

def process_payment(payment_info, amount):
    """
    Simulate a payment processing routine.
    
    In this simulation, we check the last digit of the card number.
    If the last digit is even, the payment is treated as successful.
    In production, integrate with a secure payment gateway and avoid storing raw card data.
    """
    card_number = payment_info.get('number')
    # Secure handling: do not log sensitive information.
    if card_number and card_number[-1].isdigit() and int(card_number[-1]) % 2 == 0:
        return True
    return False

def record_transaction(conn, user_id, items, total, shipping_address):
    """
    Record a successful transaction in the database.
    The cart items are stored as a JSON string.
    Returns the transaction ID for further use.
    """
    transaction_date = datetime.datetime.utcnow().isoformat()
    items_json = json.dumps(items)
    with conn:
        cur = conn.execute('''
            INSERT INTO transactions (user_id, items, total, shipping_address, transaction_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, items_json, total, shipping_address, transaction_date))
        transaction_id = cur.lastrowid
    print("Transaction recorded successfully with ID:", transaction_id)
    return transaction_id

def record_order(conn, user_id, transaction_id, order_status="Submitted"):
    """
    Record an order submission in the orders table with an initial order status.
    """
    submission_date = datetime.datetime.utcnow().isoformat()
    with conn:
        conn.execute('''
            INSERT INTO orders (transaction_id, user_id, order_status, submission_date)
            VALUES (?, ?, ?, ?)
        ''', (transaction_id, user_id, order_status, submission_date))
    print("Order recorded with status:", order_status)

def update_order_status(conn, order_id, new_status):
    """
    Update the status of an existing order.
    """
    with conn:
        conn.execute('UPDATE orders SET order_status = ? WHERE id = ?', (new_status, order_id))
    print("Order status updated to:", new_status)

def calculate_total(cart_items):
    """
    Calculate the subtotal from the cart items and add a $20 shipping fee.
    """
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    return subtotal + 20  # Fixed shipping fee

def checkout(user_id, payment_info, conn):
    """
    Perform the checkout process:
      1. Check if the user is logged in.
      2. If logged in, retrieve their saved card information.
      3. Retrieve the user's shipping address.
      4. Retrieve cart items for the user.
      5. Calculate the total (including shipping fee).
      6. Process the payment securely.
      7. If payment succeeds:
           a. Record the transaction.
           b. Submit the order by recording it with an order status.
           c. Clear the cart.
    """
    print(f"Starting checkout process for user: {user_id}")
    
    # Check if the user is logged in by verifying a non-empty user_id.
    if user_id:
        print("User is logged in, retrieving saved card information.")
        saved_card = get_user_card(conn, user_id)
        if saved_card:
            print("Saved card information found. Using saved card for payment.")
            payment_info = saved_card
        else:
            print("No saved card information found. Using provided payment info.")
    else:
        print("User is not logged in. Payment info must be provided.")
    
    # Retrieve shipping address.
    shipping_address = get_user_address(conn, user_id)
    if not shipping_address:
        print("Shipping address not found. Please update your address information.")
        return False
    
    # Retrieve cart items.
    cart_items = get_cart_items(conn, user_id)
    if not cart_items:
        print("Cart is empty. Nothing to checkout.")
        return False

    total = calculate_total(cart_items)
    print(f"Calculated total (including shipping): ${total:.2f}")
    print(f"Shipping to: {shipping_address}")
    
    # Process payment (simulate secure handling).
    if process_payment(payment_info, total):
        print("Payment processed successfully.")
        # Record the transaction and retrieve its ID.
        transaction_id = record_transaction(conn, user_id, cart_items, total, shipping_address)
        # Submit the order by recording it in the orders table.
        record_order(conn, user_id, transaction_id, order_status="Submitted")
        # Clear the cart after a successful order submission.
        clear_cart(conn, user_id)
        return True
    else:
        print("Payment failed. Checkout aborted.")
        return False

def test_checkout():
    """
    A test function to verify the complete checkout and order submission process:
      - Sets up an in-memory SQLite database.
      - Creates the necessary tables: transactions, orders, cart, user addresses, and user cards.
      - Inserts sample cart items, a shipping address, and saved card information for a test user.
      - Executes the checkout process.
      - Displays recorded transactions and orders for verification.
    """
    # Create an in-memory SQLite database for testing.
    conn = sqlite3.connect(':memory:')
    create_transaction_table(conn)
    create_order_table(conn)
    create_cart_table(conn)
    create_user_address_table(conn)
    create_user_card_table(conn)
    
    user_id = "user123"
    
    # Insert a sample shipping address for the user.
    add_user_address(conn, user_id, "123 Main St, Anytown, USA")
    
    # Insert sample saved card information for the user.
    add_user_card(conn, user_id, "4111111111111112", "12/26", "123")
    
    # Populate the cart with sample items.
    add_item_to_cart(conn, user_id, 'T-shirt', 25.0, 2)
    add_item_to_cart(conn, user_id, 'Jeans', 40.0, 1)
    
    # External payment info provided (will be overridden by saved card info if available).
    external_payment_info = {
        'number': '4111111111111111',  # Ends with '1' (would simulate a failure if used)
        'expiry': '12/24',
        'cvv': '321'
    }
    
    # Run the checkout process.
    result = checkout(user_id, external_payment_info, conn)
    if result:
        print("Checkout test succeeded.")
    else:
        print("Checkout test failed.")
    
    # Display the recorded transactions for verification.
    print("\nRecorded Transactions:")
    cursor = conn.execute('SELECT * FROM transactions')
    for row in cursor:
        print(row)
    
    # Display the recorded orders for verification.
    print("\nRecorded Orders:")
    cursor = conn.execute('SELECT * FROM orders')
    for row in cursor:
        print(row)

if __name__ == '__main__':
    test_checkout()
