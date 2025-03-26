import sqlite3
import datetime

# Constants
SHIPPING_FEE = 20.0

def create_tables(conn):
    """Creates tables if they do not exist."""
    cursor = conn.cursor()
    # Users table (simulate existing user database)
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS order_items")
    cursor.execute("DROP TABLE IF EXISTS successful_transactions")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_info TEXT  -- could be a card number or token in a real system
        )
    ''')
    # Cart table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total_amount REAL,
            shipping_fee REAL,
            shipping_address TEXT,
            status TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Order items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    ''')
    # Successful transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS successful_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            transaction_date TEXT,
            amount REAL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    ''')
    conn.commit()

def process_payment(user_id, amount):
    """
    Dummy payment processing.
    In a real scenario, this would integrate with a payment gateway.
    Here, we assume the payment is always successful.
    """
    print(f"Processing payment for user {user_id}: ${amount:.2f}")
    # simulate processing delay or logic...
    return True

def checkout_order(conn, user_id):
    """
    Process checkout:
      - Retrieve cart items for the given user.
      - Retrieve user shipping address.
      - Calculate total (subtotal + shipping fee).
      - Process payment.
      - Create order, order items, and record the transaction.
      - Clear the cart.
    """
    cursor = conn.cursor()
    
    # Retrieve cart items
    cursor.execute("SELECT product_id, product_name, quantity, price FROM cart WHERE user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        print("Cart is empty. Cannot proceed to checkout.")
        return None
    
    # Calculate subtotal
    subtotal = sum(item[2] * item[3] for item in cart_items)
    total_amount = subtotal + SHIPPING_FEE
    
    # Retrieve user shipping address
    cursor.execute("SELECT shipping_address FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        print("User not found.")
        return None
    shipping_address = user[0]
    
    print(f"User shipping address: {shipping_address}")
    print(f"Subtotal: ${subtotal:.2f}, Shipping fee: ${SHIPPING_FEE:.2f}, Total: ${total_amount:.2f}")
    
    # Process payment
    if not process_payment(user_id, total_amount):
        print("Payment failed. Please try again.")
        return None

    # Payment successful: create order
    now = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO orders (user_id, total_amount, shipping_fee, shipping_address, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, total_amount, SHIPPING_FEE, shipping_address, 'completed', now))
    order_id = cursor.lastrowid
    
    # Create order items
    for product_id, product_name, quantity, price in cart_items:
        cursor.execute('''
            INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, product_id, product_name, quantity, price))
    
    # Record successful transaction
    cursor.execute('''
        INSERT INTO successful_transactions (order_id, transaction_date, amount)
        VALUES (?, ?, ?)
    ''', (order_id, now, total_amount))
    
    # Clear user's cart
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    
    print(f"Checkout successful! Order ID: {order_id}")
    return order_id

def insert_sample_data(conn):
    """
    Inserts a test user and sample cart items for testing.
    """
    cursor = conn.cursor()
    
    # Insert sample user (simulate existing record)
    cursor.execute("INSERT OR IGNORE INTO users (id, name, shipping_address, payment_info) VALUES (1, 'Alice', '123 Main St, Anytown, USA', 'dummy_payment_token')")
    
    # Insert sample cart items for user id 1
    sample_cart = [
        (1, 101, 'Widget A', 2, 15.99),
        (1, 102, 'Widget B', 1, 45.50),
        (1, 103, 'Widget C', 3, 9.99)
    ]
    cursor.executemany("INSERT INTO cart (user_id, product_id, product_name, quantity, price) VALUES (?, ?, ?, ?, ?)", sample_cart)
    
    conn.commit()

def main():
    # Create a connection to an in-memory SQLite database.
    conn = sqlite3.connect(":memory:")
    
    # Create tables and insert sample data.
    create_tables(conn)
    insert_sample_data(conn)
    
    # Perform checkout for user with id 1.
    order_id = checkout_order(conn, 1)
    
    if order_id:
        cursor = conn.cursor()
        # Display the created order
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        print("\nOrder Record:")
        print(order)
        
        # Display the order items
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
        items = cursor.fetchall()
        print("\nOrder Items:")
        for item in items:
            print(item)
        
        # Display the successful transaction record
        cursor.execute("SELECT * FROM successful_transactions WHERE order_id = ?", (order_id,))
        transaction = cursor.fetchone()
        print("\nTransaction Record:")
        print(transaction)
    
    # Optionally, check that the cart is now empty.
    cursor.execute("SELECT * FROM cart WHERE user_id = 1")
    remaining_cart = cursor.fetchall()
    print("\nRemaining Cart Items for User 1:")
    print(remaining_cart)
    
    conn.close()

if __name__ == '__main__':
    main()
