import sqlite3
from random import choice

# Database connection
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Create necessary tables if they don't exist
def create_tables():
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS cart")
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        address TEXT NOT NULL,
                        payment_info TEXT NOT NULL
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        product_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        price REAL NOT NULL
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS cart (
                        cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        product_id INTEGER,
                        quantity INTEGER,
                        FOREIGN KEY(user_id) REFERENCES users(user_id),
                        FOREIGN KEY(product_id) REFERENCES products(product_id)
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        total_price REAL,
                        shipping_address TEXT,
                        status TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                    )''')

    conn.commit()

# Seed some sample data
def seed_data():
    # Insert sample users
    cursor.execute('INSERT OR IGNORE INTO users (user_id, name, address, payment_info) VALUES (1, "John Doe", "1234 Elm Street", "Visa **** 1234")')
    cursor.execute('INSERT OR IGNORE INTO users (user_id, name, address, payment_info) VALUES (2, "Jane Smith", "5678 Oak Avenue", "Mastercard **** 5678")')

    # Insert sample products
    cursor.execute('INSERT OR IGNORE INTO products (product_id, name, price) VALUES (1, "Laptop", 1000.00)')
    cursor.execute('INSERT OR IGNORE INTO products (product_id, name, price) VALUES (2, "Smartphone", 800.00)')
    cursor.execute('INSERT OR IGNORE INTO products (product_id, name, price) VALUES (3, "Headphones", 100.00)')

    # Insert sample cart items for user with user_id=1
    cursor.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (1, 1, 1)')
    cursor.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (1, 3, 2)')

    conn.commit()

# Function to simulate a payment process
def process_payment():
    # Simulate payment success/failure randomly
    return choice([True, False])

# Checkout function
def checkout(user_id):
    # Retrieve user information
    cursor.execute('SELECT name, address, payment_info FROM users WHERE user_id=?', (user_id,))
    user = cursor.fetchone()
    if not user:
        print("User not found!")
        return

    user_name, shipping_address, payment_info = user

    # Retrieve cart items for the user
    cursor.execute('''
        SELECT products.product_id, products.name, products.price, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.product_id
        WHERE cart.user_id = ?
    ''', (user_id,))
    cart_items = cursor.fetchall()

    if not cart_items:
        print("Cart is empty!")
        return

    # Calculate the total price of items
    total_price = sum(item[2] * item[3] for item in cart_items) + 20.00  # $20 shipping fee
    print(f"Total price including shipping: ${total_price:.2f}")

    # Process payment
    if not process_payment():
        print("Payment failed! Please try again.")
        return
    else:
        print("Payment successful!")

    # Record the order in the orders table
    cursor.execute('''
        INSERT INTO orders (user_id, total_price, shipping_address, status)
        VALUES (?, ?, ?, ?)
    ''', (user_id, total_price, shipping_address, 'Success'))
    
    # Clear the user's cart after successful order
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))

    conn.commit()
    print("Order placed successfully!")

# Initialize and seed the database
create_tables()
seed_data()

# Test the checkout functionality
checkout(1)  # User with ID 1 attempts to check out
