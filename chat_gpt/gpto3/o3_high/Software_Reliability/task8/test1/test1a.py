import sqlite3
import datetime

def create_tables(conn):
    cursor = conn.cursor()
    # Create users table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS order_items")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_info TEXT
        )
    ''')
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')
    # Create cart table (each row is an item in the user's cart)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            shipping_address TEXT,
            total REAL,
            created_at TEXT,
            payment_status TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # Create order_items table to record individual items in an order
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            unit_price REAL,
            quantity INTEGER,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    conn.commit()

def populate_dummy_data(conn):
    cursor = conn.cursor()
    # Insert a dummy user with a shipping address and payment info.
    cursor.execute(
        "INSERT INTO users (name, shipping_address, payment_info) VALUES (?, ?, ?)",
        ('John Doe', '123 Main St, Cityville', 'VISA **** 1234')
    )
    user_id = cursor.lastrowid

    # Insert dummy products.
    products = [
        ('Widget A', 10.00),
        ('Widget B', 15.50),
        ('Widget C', 7.25)
    ]
    product_ids = []
    for name, price in products:
        cursor.execute(
            "INSERT INTO products (name, price) VALUES (?, ?)",
            (name, price)
        )
        product_ids.append(cursor.lastrowid)
    
    # Insert items into the cart for our dummy user (2 of each product).
    for pid in product_ids:
        cursor.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
            (user_id, pid, 2)
        )
    conn.commit()
    return user_id

def process_payment(user_id, amount):
    # Dummy payment processing: In real-world, integrate with a payment gateway.
    print(f"Processing payment for user {user_id} for amount ${amount:.2f}...")
    return True

def checkout(user_id, conn):
    cursor = conn.cursor()
    # Retrieve cart items along with product details.
    cursor.execute('''
        SELECT p.id, p.name, p.price, c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        print("Cart is empty.")
        return

    # Calculate the subtotal for the cart items.
    subtotal = sum(item[2] * item[3] for item in cart_items)
    shipping_fee = 20.00
    total = subtotal + shipping_fee

    # Retrieve user's shipping address and payment info.
    cursor.execute("SELECT shipping_address, payment_info FROM users WHERE id = ?", (user_id,))
    user_info = cursor.fetchone()
    if not user_info:
        print("User not found.")
        return
    shipping_address, payment_info = user_info

    print("----- Checkout Summary -----")
    print("Cart Items:")
    for item in cart_items:
        product_id, name, price, quantity = item
        print(f" - {name} (ID: {product_id}), Price: ${price:.2f}, Quantity: {quantity}")
    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Shipping Fee: ${shipping_fee:.2f}")
    print(f"Total: ${total:.2f}")
    print(f"Shipping Address: {shipping_address}")

    # Process the payment.
    if not process_payment(user_id, total):
        print("Payment failed.")
        return

    # Record the order in the orders table.
    created_at = datetime.datetime.now().isoformat()
    payment_status = 'Success'
    cursor.execute('''
        INSERT INTO orders (user_id, shipping_address, total, created_at, payment_status)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, shipping_address, total, created_at, payment_status))
    order_id = cursor.lastrowid

    # Record each item in the order_items table.
    for item in cart_items:
        product_id, name, price, quantity = item
        cursor.execute('''
            INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, product_id, name, price, quantity))
    
    # Clear the cart after a successful checkout.
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()

    print("Order placed successfully!")
    print(f"Order ID: {order_id}")

if __name__ == '__main__':
    # Connect to an in-memory SQLite database for testing purposes.
    conn = sqlite3.connect(':memory:')
    create_tables(conn)
    # Populate dummy data and get the test user ID.
    user_id = populate_dummy_data(conn)
    # Run the checkout process for the test user.
    checkout(user_id, conn)
