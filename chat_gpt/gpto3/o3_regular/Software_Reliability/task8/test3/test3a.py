import sqlite3
import datetime

# --- Setup and DB initialization ---
def initialize_db(conn):
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS order_items")

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_info TEXT -- for simulation purposes
        )
    ''')
    
    # Create cart table
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
    
    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            shipping_address TEXT,
            total_amount REAL,
            order_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Create order_items table
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

# --- Seed test data ---
def seed_test_data(conn):
    cursor = conn.cursor()
    # Insert a test user (if not already exists)
    cursor.execute("SELECT COUNT(*) FROM users WHERE id = ?", (1,))
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (id, name, shipping_address, payment_info)
            VALUES (?, ?, ?, ?)
        ''', (1, "Alice", "123 Main St, Anytown, USA", "valid_card_info"))
    
    # Insert some products in the user's cart
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (1,))
    cart_items = [
        (1, 101, "Widget", 2, 15.00),
        (1, 102, "Gadget", 1, 25.00)
    ]
    cursor.executemany('''
        INSERT INTO cart (user_id, product_id, product_name, quantity, price)
        VALUES (?, ?, ?, ?, ?)
    ''', cart_items)
    
    conn.commit()

# --- Simulated payment processing ---
def process_payment(user_id, total_amount, payment_info):
    # In a real system, this function would interact with a payment gateway.
    # Here we assume payment is always successful.
    print(f"Processing payment for user {user_id} for amount ${total_amount:.2f} using {payment_info} ...")
    return True

# --- Checkout process ---
def checkout_order(conn, user_id):
    cursor = conn.cursor()
    
    # Retrieve items from the cart
    cursor.execute('''
        SELECT product_id, product_name, quantity, price
        FROM cart
        WHERE user_id = ?
    ''', (user_id,))
    cart_items = cursor.fetchall()
    
    if not cart_items:
        print("Cart is empty. Cannot proceed with checkout.")
        return
    
    # Calculate subtotal
    subtotal = sum(quantity * price for (_, _, quantity, price) in cart_items)
    shipping_fee = 20.00
    total_amount = subtotal + shipping_fee
    
    # Retrieve user shipping address and payment info
    cursor.execute('''
        SELECT shipping_address, payment_info
        FROM users
        WHERE id = ?
    ''', (user_id,))
    user_info = cursor.fetchone()
    if not user_info:
        print("User not found.")
        return
    
    shipping_address, payment_info = user_info
    
    # Simulate payment processing
    if not process_payment(user_id, total_amount, payment_info):
        print("Payment failed. Order not processed.")
        return
    
    # Record the order
    order_date = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO orders (user_id, shipping_address, total_amount, order_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, shipping_address, total_amount, order_date))
    order_id = cursor.lastrowid
    
    # Record order items
    for product_id, product_name, quantity, price in cart_items:
        cursor.execute('''
            INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, product_id, product_name, quantity, price))
    
    # Clear the cart for the user
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    
    conn.commit()
    
    print("Order processed successfully!")
    print(f"Order ID: {order_id}")
    print(f"Shipping Address: {shipping_address}")
    print(f"Total Amount Charged: ${total_amount:.2f}")

# --- Main function for testing ---
def main():
    # For self-contained testing we use an in-memory database.
    conn = sqlite3.connect(":memory:")
    initialize_db(conn)
    seed_test_data(conn)
    
    print("Starting checkout process for user 1:")
    checkout_order(conn, 1)
    
    # Optional: Verify that the order was recorded and the cart is now empty
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    print("\nRecorded Orders:")
    for order in orders:
        print(order)
    
    cursor.execute("SELECT * FROM cart")
    remaining_cart = cursor.fetchall()
    print("\nRemaining Cart Items:")
    print(remaining_cart)
    
    conn.close()

if __name__ == "__main__":
    main()
