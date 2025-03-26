import sqlite3
import datetime

def create_tables(conn):
    cursor = conn.cursor()
    # Enable foreign key support
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS carts")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS order_items")
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Users table: stores user profile info including shipping address and payment info.

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            shipping_address TEXT,
            payment_info TEXT
        );
    """)
    
    # Products table: stores product details.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL
        );
    """)
    
    # Carts table: stores current cart items for each user.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)
    
    # Orders table: stores overall order information.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            shipping_address TEXT,
            total_amount REAL,
            shipping_fee REAL,
            order_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    
    # Order_items table: stores details for each product in an order.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)
    
    conn.commit()

def seed_data(conn):
    cursor = conn.cursor()
    # Insert a test user with shipping address and dummy payment info.
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, shipping_address, payment_info)
        VALUES (?, ?, ?, ?);
    """, (1, "Alice", "123 Main St, City, Country", "valid_payment_info"))
    
    # Insert some test products.
    cursor.execute("""
        INSERT OR IGNORE INTO products (id, name, price)
        VALUES (?, ?, ?);
    """, (1, "Widget", 9.99))
    cursor.execute("""
        INSERT OR IGNORE INTO products (id, name, price)
        VALUES (?, ?, ?);
    """, (2, "Gadget", 14.99))
    
    # Insert items into the cart for the test user.
    # For example, 2 Widgets and 1 Gadget.
    cursor.execute("""
        INSERT OR IGNORE INTO carts (id, user_id, product_id, quantity)
        VALUES (?, ?, ?, ?);
    """, (1, 1, 1, 2))
    cursor.execute("""
        INSERT OR IGNORE INTO carts (id, user_id, product_id, quantity)
        VALUES (?, ?, ?, ?);
    """, (2, 1, 2, 1))
    
    conn.commit()

def simulate_payment(amount, payment_info):
    """
    Dummy payment simulation.
    In a real scenario, integrate with a payment gateway.
    """
    print(f"Simulating payment of ${amount:.2f} using payment info: {payment_info}")
    # For testing, assume the payment always succeeds.
    return True

def checkout_order(conn, user_id):
    cursor = conn.cursor()
    
    # Retrieve items from the user's cart (join with products to get name and price)
    cursor.execute("""
        SELECT c.product_id, p.name, c.quantity, p.price
        FROM carts c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?;
    """, (user_id,))
    cart_items = cursor.fetchall()
    
    if not cart_items:
        print("Cart is empty.")
        return
    
    # Retrieve user's shipping address and payment information
    cursor.execute("""
        SELECT shipping_address, payment_info FROM users WHERE id = ?;
    """, (user_id,))
    user_data = cursor.fetchone()
    if not user_data:
        print("User not found.")
        return
    shipping_address, payment_info = user_data
    
    # Calculate subtotal from the cart items
    subtotal = sum(quantity * price for (_, _, quantity, price) in cart_items)
    shipping_fee = 20.0
    total_amount = subtotal + shipping_fee
    
    # Display order summary
    print("\nOrder Summary:")
    print("------------------------")
    for product_id, name, quantity, price in cart_items:
        item_total = quantity * price
        print(f"Product: {name} (ID: {product_id}), Quantity: {quantity}, Unit Price: ${price:.2f}, Total: ${item_total:.2f}")
    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Shipping Fee: ${shipping_fee:.2f}")
    print(f"Total: ${total_amount:.2f}\n")
    
    # Process payment
    if not simulate_payment(total_amount, payment_info):
        print("Payment failed.")
        return
    
    # Record the order
    order_date = datetime.datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO orders (user_id, shipping_address, total_amount, shipping_fee, order_date)
        VALUES (?, ?, ?, ?, ?);
    """, (user_id, shipping_address, total_amount, shipping_fee, order_date))
    order_id = cursor.lastrowid
    
    # Record each order item
    for product_id, name, quantity, price in cart_items:
        total_price = quantity * price
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
            VALUES (?, ?, ?, ?, ?);
        """, (order_id, product_id, quantity, price, total_price))
    
    # Clear the user's cart after successful order placement
    cursor.execute("DELETE FROM carts WHERE user_id = ?;", (user_id,))
    
    conn.commit()
    print("Order placed successfully. Your cart has been cleared.")

def main():
    # Connect to the SQLite database (creates file 'ecommerce.db')
    conn = sqlite3.connect("ecommerce.db")
    create_tables(conn)
    seed_data(conn)
    
    # For testing, we checkout order for user with ID 1
    checkout_order(conn, 1)
    
    conn.close()

if __name__ == '__main__':
    main()
