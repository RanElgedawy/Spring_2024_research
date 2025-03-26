import sqlite3

def initialize_db(conn):
    """Creates the necessary tables for users, cart, orders, and order items."""
    c = conn.cursor()
    # Create the users table.
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS cart")
    c.execute("DROP TABLE IF EXISTS orders")
    c.execute("DROP TABLE IF EXISTS order_items")

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        shipping_address TEXT NOT NULL,
        payment_info TEXT NOT NULL
    )
    ''')
    # Create the cart table.
    c.execute('''
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    # Create the orders table.
    c.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        shipping_address TEXT NOT NULL,
        total_amount REAL NOT NULL,
        shipping_fee REAL NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    # Create the order_items table.
    c.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id)
    )
    ''')
    conn.commit()

def insert_test_data(conn):
    """Inserts a test user and a couple of items into the cart."""
    c = conn.cursor()
    # Insert a test user.
    c.execute('''
        INSERT OR IGNORE INTO users (id, name, shipping_address, payment_info)
        VALUES (?, ?, ?, ?)
    ''', (1, 'John Doe', '123 Main St, Anytown, USA', 'Visa **** 4242'))
    
    # Clear any existing cart items for the test user.
    c.execute('DELETE FROM cart WHERE user_id = ?', (1,))
    
    # Insert sample cart items.
    cart_items = [
        (1, 101, 'Widget A', 2, 10.0),  # 2 x $10.0 = $20.0
        (1, 102, 'Widget B', 1, 15.0)   # 1 x $15.0 = $15.0
    ]
    c.executemany('''
        INSERT INTO cart (user_id, product_id, product_name, quantity, price)
        VALUES (?, ?, ?, ?, ?)
    ''', cart_items)
    conn.commit()

def simulate_payment(total_amount, payment_info):
    """
    Dummy payment function.
    For testing, this function simply prints payment details and returns True.
    In a real implementation, integrate with a payment gateway here.
    """
    print(f"Processing payment of ${total_amount:.2f} using saved card info: {payment_info}")
    return True

def checkout_order(conn, user_id):
    """
    Processes checkout for a logged in user:
    - Checks if the user is logged in (user_id is provided).
    - Retrieves user profile (shipping address and saved card/payment info).
    - Retrieves current cart items.
    - Calculates the total (subtotal + $20 shipping fee).
    - Simulates payment processing.
    - If payment is successful, creates an order record, copies cart items into the order_items table,
      and clears the cart.
    """
    # Check if user is logged in.
    if not user_id:
        print("Error: User is not logged in. Please log in to proceed with checkout.")
        return

    c = conn.cursor()
    # Get user information.
    c.execute('SELECT shipping_address, payment_info FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    if not user:
        print("User not found!")
        return
    shipping_address, payment_info = user

    # Get the user's cart items.
    c.execute('SELECT product_id, product_name, quantity, price FROM cart WHERE user_id = ?', (user_id,))
    cart_items = c.fetchall()
    if not cart_items:
        print("Cart is empty!")
        return

    # Calculate subtotal, add shipping fee, and compute total.
    subtotal = sum(quantity * price for _, _, quantity, price in cart_items)
    shipping_fee = 20.0
    total_amount = subtotal + shipping_fee

    print("\n--- Cart Details ---")
    for product_id, product_name, quantity, price in cart_items:
        print(f"Product ID: {product_id}, Name: {product_name}, Quantity: {quantity}, Price: ${price:.2f}")
    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Shipping Fee: ${shipping_fee:.2f}")
    print(f"Total Amount: ${total_amount:.2f}\n")

    # Process the payment using the user's saved card information.
    if not simulate_payment(total_amount, payment_info):
        print("Payment failed!")
        return

    # Insert a new order.
    c.execute('''
    INSERT INTO orders (user_id, shipping_address, total_amount, shipping_fee, status)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, shipping_address, total_amount, shipping_fee, 'Paid'))
    order_id = c.lastrowid

    # Insert each cart item into the order_items table.
    for product_id, product_name, quantity, price in cart_items:
        c.execute('''
        INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
        VALUES (?, ?, ?, ?, ?)
        ''', (order_id, product_id, product_name, quantity, price))

    # Clear the cart after successful checkout.
    c.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    conn.commit()

    print(f"Order {order_id} has been placed successfully!")

def main():
    # Use an in-memory database for testing; switch to a file-based DB if needed.
    conn = sqlite3.connect(':memory:')
    initialize_db(conn)
    insert_test_data(conn)
    
    # Simulate checkout for a logged in user.
    logged_in_user_id = 1  # Set to None to simulate not logged in.
    print("Attempting checkout for a logged in user...")
    checkout_order(conn, logged_in_user_id)
    
    # For verification, print out the orders and order items.
    c = conn.cursor()
    print("\n--- Orders Table ---")
    for row in c.execute('SELECT * FROM orders'):
        print(row)
    
    print("\n--- Order Items Table ---")
    for row in c.execute('SELECT * FROM order_items'):
        print(row)
    
    conn.close()

if __name__ == '__main__':
    main()
