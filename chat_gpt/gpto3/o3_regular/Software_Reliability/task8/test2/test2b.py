import sqlite3
import datetime

# Setup database and tables
def create_tables(conn):
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS transactions")
    
    # Users table with shipping address and (dummy) payment info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            shipping_address TEXT,
            payment_info TEXT
        )
    ''')
    
    # Cart table: items that a user has added
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Orders table: stores orders after checkout
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            order_date TEXT,
            shipping_address TEXT,
            total_amount REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Transactions table: records successful payment transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            user_id INTEGER,
            transaction_date TEXT,
            amount REAL,
            status TEXT,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()

# Populate the database with sample data
def populate_sample_data(conn):
    cursor = conn.cursor()
    
    # Insert a sample user (if not exists)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (name, shipping_address, payment_info)
            VALUES (?, ?, ?)
        ''', ("Alice", "123 Maple Street, Springfield", "VISA **** 1234"))
    
    # Insert sample cart items for the user with id 1
    cursor.execute("SELECT COUNT(*) FROM cart WHERE user_id = ?", (1,))
    if cursor.fetchone()[0] == 0:
        sample_items = [
            (1, 101, "T-shirt", 2, 15.99),
            (1, 102, "Jeans", 1, 39.99),
            (1, 103, "Sneakers", 1, 59.99)
        ]
        cursor.executemany('''
            INSERT INTO cart (user_id, product_id, product_name, quantity, price)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_items)
    
    conn.commit()

# Simulated payment processing function (always returns True)
def process_payment(amount, payment_info):
    print(f"Processing payment of ${amount:.2f} using {payment_info}...")
    # Here you would normally integrate with a payment gateway.
    # For this example, we simulate a successful payment.
    return True

# Checkout function for a given user_id
def checkout_order(conn, user_id):
    cursor = conn.cursor()
    
    # Retrieve user info (shipping address and payment info)
    cursor.execute("SELECT shipping_address, payment_info FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        print("User not found.")
        return False
    shipping_address, payment_info = user
    
    # Retrieve current cart items for the user
    cursor.execute("SELECT product_id, product_name, quantity, price FROM cart WHERE user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        print("Cart is empty.")
        return False
    
    # Display cart items
    print("Cart items:")
    total = 0.0
    for item in cart_items:
        product_id, product_name, quantity, price = item
        subtotal = quantity * price
        total += subtotal
        print(f" - {product_name} (ID: {product_id}), Quantity: {quantity}, Unit Price: ${price:.2f}, Subtotal: ${subtotal:.2f}")
    
    # Add shipping fee
    shipping_fee = 20.0
    total_with_shipping = total + shipping_fee
    print(f"Subtotal: ${total:.2f}")
    print(f"Shipping fee: ${shipping_fee:.2f}")
    print(f"Total amount: ${total_with_shipping:.2f}")
    
    # Process payment
    if not process_payment(total_with_shipping, payment_info):
        print("Payment failed.")
        return False
    
    # Record order
    order_date = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO orders (user_id, order_date, shipping_address, total_amount)
        VALUES (?, ?, ?, ?)
    ''', (user_id, order_date, shipping_address, total_with_shipping))
    order_id = cursor.lastrowid
    
    # Record transaction
    transaction_date = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO transactions (order_id, user_id, transaction_date, amount, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (order_id, user_id, transaction_date, total_with_shipping, "SUCCESS"))
    
    # Clear the user's cart after successful order
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    
    conn.commit()
    
    print("Order successfully processed!")
    print(f"Order ID: {order_id}")
    return True

# Main function for testing
def main():
    # Connect to an in-memory database (change to a filename for persistent storage)
    conn = sqlite3.connect(":memory:")
    
    create_tables(conn)
    populate_sample_data(conn)
    
    user_id = 1  # Using our sample user with id 1
    print("\n--- Starting Checkout Process ---")
    success = checkout_order(conn, user_id)
    
    if success:
        # Optionally, show orders and transactions from the database
        cursor = conn.cursor()
        print("\nOrders:")
        for row in cursor.execute("SELECT * FROM orders"):
            print(row)
        print("\nTransactions:")
        for row in cursor.execute("SELECT * FROM transactions"):
            print(row)
    conn.close()

if __name__ == "__main__":
    main()
