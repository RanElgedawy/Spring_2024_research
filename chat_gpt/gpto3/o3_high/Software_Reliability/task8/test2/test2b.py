import sqlite3
import datetime

def setup_db(conn):
    """Create necessary tables in the database."""
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS Users")
    cur.execute("DROP TABLE IF EXISTS Products")
    cur.execute("DROP TABLE IF EXISTS Cart")
    cur.execute("DROP TABLE IF EXISTS Orders")
    cur.execute("DROP TABLE IF EXISTS OrderItems")
    cur.execute("DROP TABLE IF EXISTS Transactions")

    cur.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            shipping_address TEXT,
            payment_info TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            shipping_address TEXT,
            total REAL,
            shipping_fee REAL,
            status TEXT,
            created_at TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS OrderItems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price REAL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            status TEXT,
            amount REAL,
            created_at TEXT
        )
    ''')
    conn.commit()

def insert_sample_data(conn):
    """Insert sample user, products, and cart items for testing."""
    cur = conn.cursor()
    # Insert a sample user (user database already exists in a real scenario)
    cur.execute('''
        INSERT INTO Users (id, name, shipping_address, payment_info)
        VALUES (1, 'John Doe', '123 Main St, Anytown, USA', 'VISA ****1234')
    ''')
    # Insert sample products (assume these exist in the product catalog)
    cur.execute("INSERT INTO Products (id, name, price) VALUES (101, 'Widget', 25.00)")
    cur.execute("INSERT INTO Products (id, name, price) VALUES (102, 'Gadget', 15.50)")
    cur.execute("INSERT INTO Products (id, name, price) VALUES (103, 'Thingamajig', 7.75)")
    # Insert sample cart items for user 1 (assume these exist in the user's cart)
    cur.execute("INSERT INTO Cart (user_id, product_id, quantity) VALUES (1, 101, 2)")  # 2 Widgets
    cur.execute("INSERT INTO Cart (user_id, product_id, quantity) VALUES (1, 102, 1)")  # 1 Gadget
    cur.execute("INSERT INTO Cart (user_id, product_id, quantity) VALUES (1, 103, 3)")  # 3 Thingamajigs
    conn.commit()

def process_payment(user, amount):
    """
    Simulate payment processing.
    In a real implementation, this would integrate with a payment gateway.
    """
    print(f"Processing payment of ${amount:.2f} for {user['name']} using card {user['payment_info']}")
    # For simulation, assume payment always succeeds.
    return True

def checkout(conn, user_id):
    """
    Perform the checkout process:
      - Retrieve the user's cart items and shipping address.
      - Calculate the subtotal and add a fixed $20 shipping fee.
      - Process the payment.
      - On success, create an order, record order items and transaction, and clear the cart.
    """
    cur = conn.cursor()
    
    # Retrieve user details.
    cur.execute("SELECT id, name, shipping_address, payment_info FROM Users WHERE id=?", (user_id,))
    user = cur.fetchone()
    if not user:
        print("User not found.")
        return None
    
    user_data = {
        'id': user[0],
        'name': user[1],
        'shipping_address': user[2],
        'payment_info': user[3]
    }
    
    # Retrieve cart items joined with product details.
    cur.execute("""
        SELECT Cart.product_id, Products.name, Cart.quantity, Products.price
        FROM Cart
        JOIN Products ON Cart.product_id = Products.id
        WHERE Cart.user_id=?
    """, (user_id,))
    cart_items = cur.fetchall()
    
    if not cart_items:
        print("Cart is empty.")
        return None
    
    # Calculate the subtotal from the cart.
    subtotal = sum(quantity * price for _, _, quantity, price in cart_items)
    shipping_fee = 20.0
    total = subtotal + shipping_fee

    print(f"Cart subtotal: ${subtotal:.2f}")
    print(f"Shipping fee: ${shipping_fee:.2f}")
    print(f"Total amount: ${total:.2f}")
    
    # Process payment.
    if not process_payment(user_data, total):
        print("Payment failed.")
        return None
    
    created_at = datetime.datetime.now().isoformat()
    order_status = "Completed"
    
    # Create a new order.
    cur.execute("""
        INSERT INTO Orders (user_id, shipping_address, total, shipping_fee, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, user_data['shipping_address'], total, shipping_fee, order_status, created_at))
    order_id = cur.lastrowid
    
    # Record each order item.
    for product_id, product_name, quantity, price in cart_items:
        cur.execute("""
            INSERT INTO OrderItems (order_id, product_id, product_name, quantity, price)
            VALUES (?, ?, ?, ?, ?)
        """, (order_id, product_id, product_name, quantity, price))
    
    # Record the transaction.
    transaction_status = "Successful"
    cur.execute("""
        INSERT INTO Transactions (order_id, status, amount, created_at)
        VALUES (?, ?, ?, ?)
    """, (order_id, transaction_status, total, created_at))
    
    # Clear the user's cart.
    cur.execute("DELETE FROM Cart WHERE user_id=?", (user_id,))
    conn.commit()
    
    print(f"Order {order_id} completed successfully.")
    return order_id

def test_checkout():
    """Set up the database, insert sample data, and perform a checkout for testing."""
    # Using an in-memory SQLite database for testing.
    conn = sqlite3.connect(":memory:")
    setup_db(conn)
    insert_sample_data(conn)
    
    # Perform checkout for user with ID 1.
    order_id = checkout(conn, 1)
    if order_id:
        print("\n--- Order Details ---")
        cur = conn.cursor()
        cur.execute("SELECT * FROM Orders WHERE order_id=?", (order_id,))
        order = cur.fetchone()
        print("Order:", order)
        
        print("\n--- Order Items ---")
        cur.execute("SELECT * FROM OrderItems WHERE order_id=?", (order_id,))
        order_items = cur.fetchall()
        for item in order_items:
            print(item)
        
        print("\n--- Transaction Details ---")
        cur.execute("SELECT * FROM Transactions WHERE order_id=?", (order_id,))
        transaction = cur.fetchone()
        print("Transaction:", transaction)
    else:
        print("Checkout failed.")

if __name__ == '__main__':
    test_checkout()
