import sqlite3
from datetime import datetime

# Database initialization: creates tables if they don't exist.
def init_db(conn):
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS orders")

    # Create users table (id, name, shipping_address, payment_info)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_info TEXT NOT NULL
        )
    ''')
    
    # Create cart table (cart id, user id, product id, product name, quantity, price)
    cursor.execute('''
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
    
    # Create orders table (order id, user id, order_date, total_amount, shipping_address, payment_info)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            total_amount REAL NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_info TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()

# Dummy payment processing: always returns True (simulate success)
def process_payment(amount, payment_info):
    print(f"Processing payment of ${amount:.2f} using payment info: {payment_info}")
    # Here you could integrate with a real payment gateway.
    return True

# Checkout function: retrieves cart items and user info, calculates total (including $20 shipping fee), processes payment,
# records the order, and clears the user's cart.
def checkout_order(conn, user_id):
    cursor = conn.cursor()
    
    # Retrieve user's shipping address and payment info
    cursor.execute("SELECT shipping_address, payment_info FROM users WHERE id = ?", (user_id,))
    user_info = cursor.fetchone()
    if not user_info:
        print("User not found.")
        return
    shipping_address, payment_info = user_info
    
    # Retrieve items in the user's cart
    cursor.execute("SELECT product_id, product_name, quantity, price FROM cart WHERE user_id = ?", (user_id,))
    items = cursor.fetchall()
    if not items:
        print("Cart is empty.")
        return
    
    # Calculate subtotal
    subtotal = sum(quantity * price for (_, _, quantity, price) in items)
    shipping_fee = 20.0
    total_amount = subtotal + shipping_fee
    
    print("Cart items:")
    for item in items:
        print(f"Product ID: {item[0]}, Name: {item[1]}, Quantity: {item[2]}, Price: ${item[3]:.2f}")
    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Shipping Fee: ${shipping_fee:.2f}")
    print(f"Total Amount: ${total_amount:.2f}")
    
    # Process payment
    if process_payment(total_amount, payment_info):
        # Payment successful, record order
        order_date = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO orders (user_id, order_date, total_amount, shipping_address, payment_info)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, order_date, total_amount, shipping_address, payment_info))
        conn.commit()
        order_id = cursor.lastrowid
        print(f"Order {order_id} has been successfully placed.")
        
        # Clear the user's cart
        cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()
    else:
        print("Payment failed. Order not placed.")

# For testing functionality
if __name__ == "__main__":
    # Connect to the SQLite database (file: ecommerce.db)
    conn = sqlite3.connect("ecommerce.db")
    
    # Initialize database tables
    init_db(conn)
    
    cursor = conn.cursor()
    
    # Insert a sample user (if not already present)
    cursor.execute("SELECT id FROM users WHERE id = ?", (1,))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (id, name, shipping_address, payment_info)
            VALUES (?, ?, ?, ?)
        ''', (1, "Alice", "123 Main St, City, Country", "Visa **** 1234"))
        conn.commit()
        print("Inserted sample user.")
    
    # Insert sample cart items for the user
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (1,))  # Clear previous cart for clean testing
    sample_cart_items = [
        (1, 101, "T-Shirt", 2, 15.99),
        (1, 202, "Jeans", 1, 39.99),
        (1, 303, "Sneakers", 1, 59.99)
    ]
    cursor.executemany('''
        INSERT INTO cart (user_id, product_id, product_name, quantity, price)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_cart_items)
    conn.commit()
    print("Inserted sample cart items.\n")
    
    # Run checkout for user_id = 1
    checkout_order(conn, 1)
    
    conn.close()
