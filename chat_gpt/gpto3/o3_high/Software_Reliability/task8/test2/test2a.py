import sqlite3

DATABASE = "ecommerce.db"

def get_connection():
    """Create and return a connection to the SQLite database."""
    return sqlite3.connect(DATABASE)

def setup_database():
    """Set up the database tables and insert sample data if needed."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create the users table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS order_items")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_info TEXT NOT NULL
        )
    ''')
    
    # Create the cart table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    ''')
    
    # Create the orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            shipping_address TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create the order_items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    ''')
    
    conn.commit()
    
    # Insert a sample user if not already present
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (id, name, shipping_address, payment_info)
            VALUES (?, ?, ?, ?)
        ''', (1, "John Doe", "123 Test St, Test City, TX", "VISA ****1234"))
        conn.commit()
    
    # Insert sample cart items for user_id 1 if the cart is empty
    cursor.execute("SELECT COUNT(*) FROM cart WHERE user_id = ?", (1,))
    if cursor.fetchone()[0] == 0:
        sample_cart_items = [
            (1, 101, "Widget A", 2, 10.00),  # user_id, product_id, product_name, quantity, price
            (1, 102, "Widget B", 1, 20.00)
        ]
        cursor.executemany('''
            INSERT INTO cart (user_id, product_id, product_name, quantity, price)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_cart_items)
        conn.commit()
    
    conn.close()

def process_payment(user_id, amount):
    """
    Simulate processing a payment.
    For demonstration purposes, we assume the payment always succeeds.
    """
    print(f"Processing payment for user {user_id} for amount: ${amount:.2f}")
    return True

def checkout_order(user_id):
    """
    Processes checkout for the given user_id:
    - Retrieves cart items and the user's shipping address.
    - Calculates the total (cart subtotal + $20 shipping fee).
    - Simulates payment processing.
    - Inserts the order and order items into the database.
    - Clears the user's cart upon successful payment.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Retrieve the user's shipping address
    cursor.execute("SELECT shipping_address FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        print("User not found!")
        conn.close()
        return
    shipping_address = user[0]
    
    # Retrieve the user's cart items
    cursor.execute("SELECT product_id, product_name, quantity, price FROM cart WHERE user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        print("Cart is empty!")
        conn.close()
        return
    
    # Calculate the subtotal and total (adding a $20 shipping fee)
    subtotal = sum(quantity * price for (_, _, quantity, price) in cart_items)
    shipping_fee = 20.00
    total_amount = subtotal + shipping_fee
    print(f"Subtotal: ${subtotal:.2f}, Shipping Fee: ${shipping_fee:.2f}, Total: ${total_amount:.2f}")
    
    # Process the payment
    if not process_payment(user_id, total_amount):
        print("Payment failed!")
        conn.close()
        return
    
    # Insert a new order record
    cursor.execute('''
        INSERT INTO orders (user_id, total_amount, shipping_address)
        VALUES (?, ?, ?)
    ''', (user_id, total_amount, shipping_address))
    order_id = cursor.lastrowid
    
    # Insert each cart item into the order_items table
    order_items = []
    for product_id, product_name, quantity, price in cart_items:
        order_items.append((order_id, product_id, product_name, quantity, price))
    cursor.executemany('''
        INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
        VALUES (?, ?, ?, ?, ?)
    ''', order_items)
    
    # Clear the user's cart after successful order placement
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    
    conn.commit()
    conn.close()
    
    print(f"Order {order_id} has been placed successfully!")

def main():
    # Set up database and sample data
    setup_database()
    
    # Testing the checkout process for a sample user (user_id = 1)
    user_id = 1
    print("Initiating checkout for user_id =", user_id)
    checkout_order(user_id)
    
    # Display the orders and order items to verify the transaction
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n--- Orders ---")
    cursor.execute("SELECT * FROM orders")
    for order in cursor.fetchall():
        print(order)
    
    print("\n--- Order Items ---")
    cursor.execute("SELECT * FROM order_items")
    for item in cursor.fetchall():
        print(item)
    
    conn.close()

if __name__ == "__main__":
    main()
