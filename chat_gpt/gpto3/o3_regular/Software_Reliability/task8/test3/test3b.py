import sqlite3
import datetime

# ---------- Database Setup and Table Creation ----------

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS order_items")

    # Users table: stores basic info including shipping address
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_info TEXT  -- dummy field for payment info
        )
    ''')
    
    # Cart table: items added by users
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

    # Orders table: stores order summary
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            shipping_address TEXT,
            total REAL,
            order_date TEXT,
            payment_success INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Order items table: details of each order
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
    
    conn.commit()

# ---------- Dummy Data for Testing ----------

def insert_sample_data(conn):
    cursor = conn.cursor()
    # Insert sample user (if not already exists)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (name, shipping_address, payment_info)
            VALUES (?, ?, ?)
        ''', ("John Doe", "123 Main St, Anytown, USA", "dummy_card_info"))
    
    # Insert sample cart items for the user (user_id=1)
    cursor.execute("SELECT COUNT(*) FROM cart WHERE user_id = 1")
    if cursor.fetchone()[0] == 0:
        sample_items = [
            (1, 101, "Widget", 2, 15.99),
            (1, 102, "Gadget", 1, 29.99),
            (1, 103, "Doodad", 3, 9.99)
        ]
        cursor.executemany('''
            INSERT INTO cart (user_id, product_id, product_name, quantity, price)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_items)
    conn.commit()

# ---------- Dummy Payment Function ----------

def process_payment(user_id, amount):
    """
    Simulate a payment process.
    In real implementation, integrate with a payment gateway.
    """
    print(f"Processing payment for user {user_id} for amount ${amount:.2f}...")
    # For simulation purposes, always return success.
    return True

# ---------- Checkout Function ----------

def checkout(conn, user_id):
    cursor = conn.cursor()
    
    # Retrieve cart items for the user
    cursor.execute('''
        SELECT product_id, product_name, quantity, price 
        FROM cart 
        WHERE user_id = ?
    ''', (user_id,))
    cart_items = cursor.fetchall()
    
    if not cart_items:
        print("Cart is empty. Cannot proceed with checkout.")
        return
    
    # Retrieve user's shipping address
    cursor.execute('''
        SELECT shipping_address 
        FROM users 
        WHERE id = ?
    ''', (user_id,))
    user_info = cursor.fetchone()
    if not user_info:
        print("User not found.")
        return
    shipping_address = user_info[0]
    
    # Calculate subtotal
    subtotal = sum(quantity * price for _, _, quantity, price in cart_items)
    shipping_fee = 20.0
    total_amount = subtotal + shipping_fee
    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Shipping Fee: ${shipping_fee:.2f}")
    print(f"Total Amount: ${total_amount:.2f}")
    
    # Process payment
    payment_success = process_payment(user_id, total_amount)
    
    if not payment_success:
        print("Payment failed. Please try again.")
        return
    
    # Payment succeeded, so create order record
    order_date = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO orders (user_id, shipping_address, total, order_date, payment_success)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, shipping_address, total_amount, order_date, 1))
    order_id = cursor.lastrowid
    
    # Insert each cart item into order_items
    for product_id, product_name, quantity, price in cart_items:
        cursor.execute('''
            INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, product_id, product_name, quantity, price))
    
    # Clear user's cart
    cursor.execute('''
        DELETE FROM cart 
        WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    print(f"Order {order_id} submitted successfully!")

# ---------- Main Function for Testing ----------

def main():
    # Connect to an in-memory SQLite database for testing (change to a file-based DB if needed)
    conn = sqlite3.connect(':memory:')
    
    create_tables(conn)
    insert_sample_data(conn)
    
    print("Before checkout, cart items:")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cart WHERE user_id = 1")
    for row in cursor.fetchall():
        print(row)
    
    print("\nInitiating checkout for user 1...\n")
    checkout(conn, 1)
    
    print("\nAfter checkout, cart items (should be empty):")
    cursor.execute("SELECT * FROM cart WHERE user_id = 1")
    cart_after = cursor.fetchall()
    print(cart_after)
    
    print("\nOrder records:")
    cursor.execute("SELECT * FROM orders")
    for order in cursor.fetchall():
        print(order)
    
    print("\nOrder items records:")
    cursor.execute("SELECT * FROM order_items")
    for order_item in cursor.fetchall():
        print(order_item)
    
    conn.close()

if __name__ == '__main__':
    main()
