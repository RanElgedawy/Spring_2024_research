import sqlite3
import datetime

def setup_database(conn):
    """Create necessary tables if they do not exist."""
    c = conn.cursor()
    
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS cart")
    c.execute("DROP TABLE IF EXISTS orders")
    c.execute("DROP TABLE IF EXISTS order_items")
    
    # Create users table with a column for saved card information.
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            shipping_address TEXT,
            card_info TEXT
        )
    ''')
    # Create cart table
    c.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    # Create orders table with an order_status field.
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            shipping_address TEXT,
            total_amount REAL,
            order_date TEXT,
            order_status TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    # Create order_items table
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY (order_id) REFERENCES orders (order_id)
        )
    ''')
    conn.commit()

def populate_dummy_data(conn):
    """Insert dummy user and cart data for testing."""
    c = conn.cursor()
    # Insert dummy users if table is empty
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        users = [
            # Format: (user_id, name, shipping_address, card_info)
            (1, 'Alice', '123 Main St, Cityville, Country', 'visa_1234'),
            (2, 'Bob', '456 Side St, Townsville, Country', 'master_5678')
        ]
        c.executemany(
            "INSERT INTO users (user_id, name, shipping_address, card_info) VALUES (?, ?, ?, ?)",
            users
        )
    # Insert dummy cart items for user_id 1 if the cart is empty for that user
    c.execute("SELECT COUNT(*) FROM cart WHERE user_id = 1")
    if c.fetchone()[0] == 0:
        cart_items = [
            # Format: (user_id, product_id, product_name, quantity, price)
            (1, 101, 'Widget', 2, 19.99),
            (1, 102, 'Gadget', 1, 29.99)
        ]
        c.executemany(
            "INSERT INTO cart (user_id, product_id, product_name, quantity, price) VALUES (?, ?, ?, ?, ?)",
            cart_items
        )
    conn.commit()

def simulate_payment(amount, card_info):
    """
    Simulate a payment process.
    In a real-world scenario, integrate with a payment gateway using the saved card info.
    Here we simply print the details and return True to indicate success.
    """
    print(f"Processing payment of ${amount:.2f} using saved card {card_info}...")
    return True

def submit_order(conn, order_id):
    """
    Submit the order by updating the order status.
    This function simulates the order submission part which records
    the successful transaction in the orders table.
    """
    c = conn.cursor()
    # Update order status to 'Submitted'
    c.execute("UPDATE orders SET order_status = ? WHERE order_id = ?", ("Submitted", order_id))
    conn.commit()
    print(f"Order {order_id} submission recorded successfully with status 'Submitted'.")

def checkout_order(conn, user_id):
    """
    Process the checkout:
      - Check if the user is logged in.
      - Retrieve the user's shipping address and saved card information.
      - Retrieve cart items, calculate the total (including a $20 shipping fee),
        and simulate payment processing.
      - Record the order and order items in the database.
      - Call the order submission part to update the order status.
      - Clear the user's cart.
    """
    # Check if the user is logged in (simulated by user_id not being None)
    if user_id is None:
        print("User is not logged in. Please log in to proceed with checkout.")
        return

    c = conn.cursor()
    
    # Retrieve user's shipping address and saved card information
    c.execute("SELECT shipping_address, card_info FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        print("User not found.")
        return
    shipping_address, card_info = user

    # Retrieve items in the user's cart
    c.execute("SELECT product_id, product_name, quantity, price FROM cart WHERE user_id = ?", (user_id,))
    cart_items = c.fetchall()
    if not cart_items:
        print("Cart is empty.")
        return

    print("\nCart items:")
    total = 0.0
    for item in cart_items:
        product_id, product_name, quantity, price = item
        item_total = quantity * price
        print(f" - {product_name} (ID: {product_id}), Quantity: {quantity}, Unit Price: ${price:.2f}, Item Total: ${item_total:.2f}")
        total += item_total

    # Apply a fixed shipping fee of $20
    shipping_fee = 20.0
    total += shipping_fee
    print(f"\nShipping fee: ${shipping_fee:.2f}")
    print(f"Total amount to be charged: ${total:.2f}")

    # Process the payment using the saved card information
    if not simulate_payment(total, card_info):
        print("Payment failed. Order not placed.")
        return

    # Record the order with an initial status of 'Pending'
    order_date = datetime.datetime.now().isoformat()
    c.execute(
        "INSERT INTO orders (user_id, shipping_address, total_amount, order_date, order_status) VALUES (?, ?, ?, ?, ?)",
        (user_id, shipping_address, total, order_date, "Pending")
    )
    order_id = c.lastrowid

    # Record each cart item in the order_items table
    for item in cart_items:
        product_id, product_name, quantity, price = item
        c.execute(
            "INSERT INTO order_items (order_id, product_id, product_name, quantity, price) VALUES (?, ?, ?, ?, ?)",
            (order_id, product_id, product_name, quantity, price)
        )
    
    # Clear the user's cart
    c.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    
    print(f"\nOrder {order_id} has been recorded successfully with initial status 'Pending'.")
    
    # Submit the order by updating the order status
    submit_order(conn, order_id)

def main():
    # Create an in-memory SQLite database.
    # For persistent storage, replace ":memory:" with a database filename.
    conn = sqlite3.connect(":memory:")
    
    # Set up tables and populate with dummy data
    setup_database(conn)
    populate_dummy_data(conn)
    
    # Simulate a logged in user.
    # For testing, change this value to None to simulate a user who is not logged in.
    logged_in_user_id = 1

    # Proceed with checkout if user is logged in
    checkout_order(conn, logged_in_user_id)

    # For testing, display stored orders and order items.
    c = conn.cursor()
    print("\n--- Orders in Database ---")
    for order in c.execute("SELECT * FROM orders"):
        print(order)
    
    print("\n--- Order Items in Database ---")
    for order_item in c.execute("SELECT * FROM order_items"):
        print(order_item)

if __name__ == "__main__":
    main()