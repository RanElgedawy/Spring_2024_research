import sqlite3

def init_db(db_name=":memory:"):
    """Initialize the database and create required tables."""
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("DROP TABLE IF EXISTS cart")
    cur.execute("DROP TABLE IF EXISTS orders")
    cur.execute("DROP TABLE IF EXISTS order_items")

    # Create users table with shipping and payment information
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        shipping_address TEXT,
        payment_info TEXT
    )
    """)
    
    # Create products table with product details
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        price REAL
    )
    """)
    
    # Create cart table that links users with products and quantities
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)
    
    # Create orders table to record the order summary
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        shipping_address TEXT,
        total_amount REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    # Create order_items table to record each product in an order
    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        product_name TEXT,
        quantity INTEGER,
        price REAL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)
    
    conn.commit()
    return conn

def populate_test_data(conn):
    """Insert sample user, product, and cart data for testing."""
    cur = conn.cursor()
    
    # Insert a test user if not already present
    cur.execute("SELECT COUNT(*) FROM users WHERE id = 1")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO users (id, name, shipping_address, payment_info) 
        VALUES (1, 'John Doe', '123 Main St, Anytown, USA', 'VISA **** 1234')
        """)
    
    # Insert test products
    products = [
        (1, "Widget A", 10.0),
        (2, "Widget B", 15.0),
        (3, "Widget C", 7.5)
    ]
    for prod in products:
        cur.execute("INSERT OR IGNORE INTO products (id, name, price) VALUES (?, ?, ?)", prod)
    
    # Insert test cart items for user 1: e.g., 2 of product 1 and 1 of product 3.
    # Clear previous cart entries for testing.
    cur.execute("DELETE FROM cart WHERE user_id = 1")
    cart_items = [
        (1, 1, 2),  # (user_id, product_id, quantity)
        (1, 3, 1)
    ]
    for item in cart_items:
        cur.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)", item)
    
    conn.commit()

def process_payment(amount, payment_info):
    """
    Simulate a payment processing step.
    In a real-world scenario, this function would integrate with a payment gateway.
    """
    print(f"Processing payment of ${amount:.2f} using payment info: {payment_info}")
    # Simulate a successful payment
    return True

def checkout_order(conn, user_id):
    """Perform the checkout process for a given user."""
    cur = conn.cursor()
    
    # Retrieve user's shipping address and payment information
    cur.execute("SELECT shipping_address, payment_info FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    if not user:
        print("User not found.")
        return False
    
    shipping_address, payment_info = user
    
    # Retrieve cart items along with product details
    cur.execute("""
    SELECT c.product_id, p.name, p.price, c.quantity
    FROM cart c
    JOIN products p ON c.product_id = p.id
    WHERE c.user_id = ?
    """, (user_id,))
    cart_items = cur.fetchall()
    
    if not cart_items:
        print("Cart is empty.")
        return False
    
    # Calculate total: sum(product price * quantity) plus a fixed $20 shipping fee
    items_total = sum(price * quantity for _, _, price, quantity in cart_items)
    shipping_fee = 20.0
    total_amount = items_total + shipping_fee
    
    print("Cart items:")
    for product_id, name, price, quantity in cart_items:
        print(f"  Product ID: {product_id}, Name: {name}, Price: ${price:.2f}, Quantity: {quantity}")
    print(f"Items total: ${items_total:.2f}")
    print(f"Shipping fee: ${shipping_fee:.2f}")
    print(f"Total amount: ${total_amount:.2f}")
    
    # Process the payment
    if not process_payment(total_amount, payment_info):
        print("Payment failed.")
        return False
    
    # Record the order in the orders table
    cur.execute("""
    INSERT INTO orders (user_id, shipping_address, total_amount)
    VALUES (?, ?, ?)
    """, (user_id, shipping_address, total_amount))
    order_id = cur.lastrowid
    
    # Record each item from the cart into the order_items table
    for product_id, name, price, quantity in cart_items:
        cur.execute("""
        INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
        VALUES (?, ?, ?, ?, ?)
        """, (order_id, product_id, name, quantity, price))
    
    # Clear the cart after a successful checkout
    cur.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    
    print(f"Order {order_id} has been successfully placed.")
    return True

if __name__ == "__main__":
    # Initialize the database (using an in-memory database for testing)
    conn = init_db(":memory:")
    
    # Populate the database with test data
    populate_test_data(conn)
    
    # Run the checkout process for user with ID 1
    print("Starting checkout process for user 1...\n")
    checkout_order(conn, 1)
    
    # For testing, display all orders and order items recorded
    cur = conn.cursor()
    print("\nOrders:")
    for row in cur.execute("SELECT * FROM orders"):
        print(row)
    
    print("\nOrder Items:")
    for row in cur.execute("SELECT * FROM order_items"):
        print(row)
    
    conn.close()
