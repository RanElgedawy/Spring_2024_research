import sqlite3
import datetime

# --- Database Initialization ---
def init_db(conn):
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS carts")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS order_items")
    cursor.execute("DROP TABLE IF EXISTS transactions")

    # Create users table (simulate a user database with profile and payment info)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_info TEXT
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')
    
    # Create carts table (each row is an item in the cart)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            cart_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(product_id) REFERENCES products(product_id)
        )
    ''')
    
    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            shipping_address TEXT NOT NULL,
            total_amount REAL NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Create order_items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(order_id)
        )
    ''')
    
    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_date TEXT NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(order_id)
        )
    ''')
    
    conn.commit()


# --- Insert Test Data ---
def insert_test_data(conn):
    cursor = conn.cursor()
    
    # Insert a test user
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, name, shipping_address, payment_info)
        VALUES (1, 'Alice', '123 Main St, Anytown, USA', 'VISA **** 1234')
    ''')
    
    # Insert some test products
    products = [
        (1, 'Widget', 10.0),
        (2, 'Gadget', 15.0),
        (3, 'Thingamajig', 20.0)
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO products (product_id, name, price)
        VALUES (?, ?, ?)
    ''', products)
    
    # Insert items into the cart for user 1
    cart_items = [
        (1, 1, 2),  # 2 Widgets
        (1, 2, 1),  # 1 Gadget
    ]
    for user_id, product_id, quantity in cart_items:
        cursor.execute('''
            INSERT INTO carts (user_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', (user_id, product_id, quantity))
    
    conn.commit()


# --- Checkout Functionality ---
def checkout_order(conn, user_id):
    cursor = conn.cursor()
    
    # Retrieve cart items for the user (joining products to get product details)
    cursor.execute('''
        SELECT c.cart_id, p.product_id, p.name, c.quantity, p.price
        FROM carts c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = ?
    ''', (user_id,))
    cart_items = cursor.fetchall()
    
    if not cart_items:
        print("Cart is empty.")
        return

    print("Cart Items:")
    total = 0
    for cart_id, product_id, name, quantity, price in cart_items:
        subtotal = quantity * price
        total += subtotal
        print(f"Product ID: {product_id}, Name: {name}, Quantity: {quantity}, Unit Price: ${price:.2f}, Subtotal: ${subtotal:.2f}")
    
    # Add shipping fee
    shipping_fee = 20.0
    total += shipping_fee
    print(f"\nShipping Fee: ${shipping_fee:.2f}")
    print(f"Total Amount: ${total:.2f}\n")
    
    # Retrieve user's shipping address
    cursor.execute('''
        SELECT shipping_address, payment_info
        FROM users
        WHERE user_id = ?
    ''', (user_id,))
    user_info = cursor.fetchone()
    if not user_info:
        print("User not found.")
        return
    
    shipping_address, payment_info = user_info
    print(f"Shipping Address: {shipping_address}")
    print(f"Payment Info: {payment_info}\n")
    
    # Simulate payment processing (here we assume payment is always successful)
    payment_successful = True
    if payment_successful:
        order_date = datetime.datetime.now().isoformat()
        # Insert order
        cursor.execute('''
            INSERT INTO orders (user_id, shipping_address, total_amount, order_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, shipping_address, total, order_date))
        order_id = cursor.lastrowid
        
        # Insert order items
        for cart_id, product_id, name, quantity, price in cart_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, product_id, name, quantity, price))
        
        # Insert transaction record
        transaction_date = datetime.datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO transactions (order_id, status, amount, transaction_date)
            VALUES (?, ?, ?, ?)
        ''', (order_id, 'Success', total, transaction_date))
        
        # Clear the user's cart
        cursor.execute('''
            DELETE FROM carts WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        print("Payment successful! Order submitted.")
        print(f"Order ID: {order_id}")
    else:
        print("Payment failed. Please try again.")

        
# --- Testing the Functionality ---
def main():
    # Connect to an in-memory SQLite database (use a file if persistence is needed)
    conn = sqlite3.connect(':memory:')
    
    init_db(conn)
    insert_test_data(conn)
    
    # Simulate checkout for user with user_id=1
    checkout_order(conn, user_id=1)
    
    # Verify order and transaction entries (for testing purposes)
    cursor = conn.cursor()
    print("\nOrders Table:")
    for row in cursor.execute("SELECT * FROM orders"):
        print(row)
    
    print("\nOrder Items Table:")
    for row in cursor.execute("SELECT * FROM order_items"):
        print(row)
    
    print("\nTransactions Table:")
    for row in cursor.execute("SELECT * FROM transactions"):
        print(row)
    
    # Verify that the cart is empty after checkout
    cursor.execute("SELECT * FROM carts WHERE user_id = ?", (1,))
    remaining_cart = cursor.fetchall()
    print("\nRemaining Cart Items:", remaining_cart)
    
    conn.close()

if __name__ == '__main__':
    main()
