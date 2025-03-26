import sqlite3

# Function to initialize the database
def initialize_database():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    # For the sake of not conflicting with previously existing tables
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")

    # Create users table with test data
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, shipping_address TEXT, payment_info TEXT)''')
    c.execute('''INSERT INTO users (username, shipping_address, payment_info) VALUES (?, ?, ?)''',
              ('test_user', '123 Test Street, Test City', '1234567890123456'))  # Test payment info

    # Create products table with test data
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL)''')
    c.execute('''INSERT INTO products (name, price) VALUES (?, ?)''',
              ('Test Product 1', 10.99))  # Test product 1
    c.execute('''INSERT INTO products (name, price) VALUES (?, ?)''',
              ('Test Product 2', 20.49))  # Test product 2

    # Create orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER, quantity INTEGER)''')

    # Create transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY, order_id INTEGER, amount REAL, status TEXT)''')

    conn.commit()
    conn.close()

# Function to retrieve items in the user's cart
def get_cart_items(user_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute('''SELECT products.id, products.name, products.price, COUNT(orders.product_id) AS quantity
                 FROM orders
                 INNER JOIN products ON orders.product_id = products.id
                 WHERE orders.user_id = ?
                 GROUP BY products.id''', (user_id,))
    
    cart_items = c.fetchall()

    conn.close()
    return cart_items

# Function to retrieve user's shipping address
def get_shipping_address(user_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute('''SELECT shipping_address FROM users WHERE id = ?''', (user_id,))
    address = c.fetchone()[0]

    conn.close()
    return address

# Function to process payment
def process_payment(user_id, amount):
    # Implement payment processing logic here
    # For simplicity, let's assume payment is always successful
    return True

# Function to checkout order
def checkout_order(user_id):
    # Check if user is logged in
    if user_id is None:
        print("User is not logged in. Please log in to proceed with checkout.")
        return

    # Check if user has saved card information
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''SELECT payment_info FROM users WHERE id = ?''', (user_id,))
    payment_info = c.fetchone()[0]
    conn.close()

    if payment_info is None:
        print("No saved card information found. Please add a payment method to proceed with checkout.")
        return

    # Get cart items
    cart_items = get_cart_items(user_id)

    # Calculate total amount
    total_amount = sum(item[2] * item[3] for item in cart_items) + 20  # Add $20 shipping fee

    # Process payment
    if process_payment(user_id, total_amount):
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()

        # Insert order for each item in the cart
        for item in cart_items:
            product_id, quantity = item
            c.execute('''INSERT INTO orders (user_id, product_id, quantity) VALUES (?, ?, ?)''', (user_id, product_id, quantity))
            order_id = c.lastrowid  # Retrieve the last inserted row id, which is the order_id

            # Insert transaction
            c.execute('''INSERT INTO transactions (order_id, amount, status) VALUES (?, ?, ?)''', (order_id, total_amount, 'success'))

        conn.commit()
        conn.close()

        print("Order successfully placed!")
    else:
        print("Payment failed. Order not placed.")

# Test the functionality
if __name__ == "__main__":
    initialize_database()

    # Assume user with id 1 is checking out
    user_id = 1
    checkout_order(user_id)