import sqlite3
from datetime import datetime

def create_tables(conn):
    """Create necessary tables if they don't exist."""
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS cart")
    c.execute("DROP TABLE IF EXISTS orders")
    c.execute("DROP TABLE IF EXISTS order_items")
   
    # Users table: Contains user profile information including shipping address and payment info.
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            shipping_address TEXT,
            payment_info TEXT
        )
    ''')
    # Products table: Contains product details.
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL
        )
    ''')
    # Cart table: Each record represents a product added to a user's cart.
    c.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    # Orders table: Records each order placed.
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            shipping_address TEXT,
            total REAL,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Order items table: Records details for each item in an order.
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            order_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    ''')
    conn.commit()

def seed_data(conn):
    """Insert sample data for testing."""
    c = conn.cursor()
    # Insert a sample user (if not already exists)
    c.execute("SELECT * FROM users WHERE id = 1")
    if not c.fetchone():
        c.execute("""
            INSERT INTO users (id, name, shipping_address, payment_info) 
            VALUES (1, 'John Doe', '123 Main St, City, Country', 'VISA ****1234')
        """)
    # Insert sample products (using INSERT OR IGNORE to avoid duplicate entries)
    products = [
        (1, 'Laptop', 999.99),
        (2, 'Smartphone', 499.99),
        (3, 'Headphones', 149.99)
    ]
    for prod in products:
        c.execute("INSERT OR IGNORE INTO products (id, name, price) VALUES (?, ?, ?)", prod)
    # Insert sample items into the cart for user 1
    cart_items = [
        (1, 1, 1),  # 1 Laptop
        (1, 3, 2)   # 2 Headphones
    ]
    # Clear cart first to avoid duplicate seeding on multiple runs.
    c.execute("DELETE FROM cart WHERE user_id = 1")
    for item in cart_items:
        c.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)", item)
    conn.commit()

def process_payment(user_id, amount):
    """Simulate payment processing."""
    print(f"Processing payment for user {user_id} for amount ${amount:.2f}...")
    # In a real application, you would integrate with a payment gateway here.
    # For simulation, we assume payment always succeeds.
    return True

def checkout_order(conn, user_id):
    """Perform the checkout: retrieve cart items, compute total, process payment, record order."""
    c = conn.cursor()
    # Retrieve cart items along with product details.
    c.execute('''
        SELECT p.id, p.name, p.price, c.quantity 
        FROM cart c 
        JOIN products p ON c.product_id = p.id 
        WHERE c.user_id = ?
    ''', (user_id,))
    cart_items = c.fetchall()
    if not cart_items:
        print("Cart is empty.")
        return

    # Retrieve the user's shipping address.
    c.execute("SELECT shipping_address FROM users WHERE id = ?", (user_id,))
    user_info = c.fetchone()
    if not user_info:
        print("User not found.")
        return
    shipping_address = user_info[0]

    # Calculate order totals.
    subtotal = sum(item[2] * item[3] for item in cart_items)
    shipping_fee = 20.0
    total = subtotal + shipping_fee

    # Display order summary.
    print("Order Summary:")
    for item in cart_items:
        print(f"Product ID: {item[0]}, Name: {item[1]}, Price: ${item[2]:.2f}, Quantity: {item[3]}")
    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Shipping Fee: ${shipping_fee:.2f}")
    print(f"Total: ${total:.2f}\n")

    # Process the payment.
    if process_payment(user_id, total):
        timestamp = datetime.now().isoformat()
        # Insert the order record.
        c.execute("""
            INSERT INTO orders (user_id, shipping_address, total, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, shipping_address, total, timestamp))
        order_id = c.lastrowid

        # Record each order item.
        for item in cart_items:
            c.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, item[0], item[1], item[3], item[2]))
        # Clear the user's cart.
        c.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()
        print("Order has been successfully placed.")
    else:
        print("Payment failed.")

def test_checkout():
    """Function to test the checkout process."""
    # Connect to the SQLite database (creates 'ecommerce.db' in the current directory).
    conn = sqlite3.connect("ecommerce.db")
    create_tables(conn)
    seed_data(conn)
    # For this test, we use user_id 1.
    checkout_order(conn, 1)
    conn.close()

if __name__ == "__main__":
    test_checkout()
