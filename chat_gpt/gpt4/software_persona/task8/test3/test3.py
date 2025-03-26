import sqlite3
from datetime import datetime

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute("DROP TABLE IF EXISTS products")
cursor.execute("DROP TABLE IF EXISTS carts")
cursor.execute("DROP TABLE IF EXISTS orders")
cursor.execute("DROP TABLE IF EXISTS transactions")

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    shipping_address TEXT NOT NULL,
    payment_info TEXT NOT NULL,
    logged_in BOOLEAN NOT NULL DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS carts (
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    total_amount REAL,
    shipping_address TEXT,
    order_date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    payment_status TEXT,
    transaction_date TEXT,
    FOREIGN KEY(order_id) REFERENCES orders(id)
)
''')

conn.commit()

# Helper function to simulate adding test data
def add_test_data():
    cursor.execute("INSERT INTO users (username, email, shipping_address, payment_info, logged_in) VALUES (?, ?, ?, ?, ?)", 
                   ('johndoe', 'john@example.com', '1234 Elm Street, Springfield, USA', 'valid_card_info', 1))
    
    cursor.execute("INSERT INTO products (name, price) VALUES (?, ?)", ('Widget A', 10.0))
    cursor.execute("INSERT INTO products (name, price) VALUES (?, ?)", ('Widget B', 15.0))
    
    cursor.execute("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)", (1, 1, 2))  # 2x Widget A
    cursor.execute("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)", (1, 2, 1))  # 1x Widget B
    
    conn.commit()

# Function to handle the checkout process
def checkout(user_id):
    # Check if user is logged in
    cursor.execute('SELECT logged_in FROM users WHERE id = ?', (user_id,))
    user_status = cursor.fetchone()
    
    if not user_status or not user_status[0]:
        print("User is not logged in!")
        return
    
    # Retrieve user's cart items
    cursor.execute('''
    SELECT products.id, products.name, products.price, carts.quantity
    FROM carts
    JOIN products ON carts.product_id = products.id
    WHERE carts.user_id = ?
    ''', (user_id,))
    cart_items = cursor.fetchall()

    if not cart_items:
        print("Cart is empty!")
        return

    # Calculate total price
    total_price = sum(item[2] * item[3] for item in cart_items)
    shipping_fee = 20.0
    total_price += shipping_fee

    # Retrieve user's shipping address and payment info
    cursor.execute('SELECT shipping_address, payment_info FROM users WHERE id = ?', (user_id,))
    user_info = cursor.fetchone()
    shipping_address = user_info[0]
    payment_info = user_info[1]

    # Simulate payment processing using saved payment info
    if payment_info == 'valid_card_info':
        payment_successful = True  # Assume payment is successful
    else:
        payment_successful = False

    if payment_successful:
        # Record the order
        order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO orders (user_id, total_amount, shipping_address, order_date) 
        VALUES (?, ?, ?, ?)
        ''', (user_id, total_price, shipping_address, order_date))
        order_id = cursor.lastrowid
        
        # Record the transaction
        transaction_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO transactions (order_id, payment_status, transaction_date) 
        VALUES (?, ?, ?)
        ''', (order_id, 'Success', transaction_date))

        # Clear the user's cart
        cursor.execute('DELETE FROM carts WHERE user_id = ?', (user_id,))
        
        conn.commit()

        print(f"Order placed successfully! Order ID: {order_id}")
    else:
        print("Payment failed!")

# Test the checkout process
if __name__ == '__main__':
    # Add test data
    add_test_data()
    
    # Simulate checkout for user with ID 1
    checkout(1)

    # Verify the contents of the orders and transactions tables
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    print("Orders:", orders)

    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    print("Transactions:", transactions)

# Close the database connection when done
conn.close()