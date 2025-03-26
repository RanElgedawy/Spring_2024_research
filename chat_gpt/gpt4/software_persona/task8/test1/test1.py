import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute("DROP TABLE IF EXISTS products")
cursor.execute("DROP TABLE IF EXISTS cart")
cursor.execute("DROP TABLE IF EXISTS orders")
cursor.execute("DROP TABLE IF EXISTS order_items")

# Create tables if they don't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    shipping_address TEXT NOT NULL,
    payment_info TEXT NOT NULL,
    logged_in BOOLEAN NOT NULL DEFAULT 0
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total_price REAL NOT NULL,
    shipping_address TEXT NOT NULL,
    payment_status TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
)''')

# Insert some test data
cursor.execute("INSERT OR IGNORE INTO users (username, shipping_address, payment_info, logged_in) VALUES ('test_user', '123 Test St', 'VISA', 1)")
cursor.execute("INSERT OR IGNORE INTO products (name, price) VALUES ('Product 1', 50.0)")
cursor.execute("INSERT OR IGNORE INTO products (name, price) VALUES ('Product 2', 30.0)")
cursor.execute("INSERT OR IGNORE INTO cart (user_id, product_id, quantity) VALUES (1, 1, 2)")  # 2x Product 1
cursor.execute("INSERT OR IGNORE INTO cart (user_id, product_id, quantity) VALUES (1, 2, 1)")  # 1x Product 2

conn.commit()

def checkout(user_id):
    # Check if the user is logged in
    cursor.execute("SELECT logged_in, shipping_address, payment_info FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user or not user[0]:  # Check if user exists and is logged in
        print("User is not logged in or does not exist")
        return

    logged_in, shipping_address, payment_info = user

    # Retrieve items in cart
    cursor.execute('''SELECT products.id, products.name, products.price, cart.quantity
                      FROM cart
                      JOIN products ON cart.product_id = products.id
                      WHERE cart.user_id = ?''', (user_id,))
    cart_items = cursor.fetchall()

    if not cart_items:
        print("Cart is empty")
        return

    # Calculate total price
    total_price = sum(item[2] * item[3] for item in cart_items) + 20  # Add $20 shipping fee

    # Simulate payment processing using saved card information (dummy success)
    print(f"Processing payment using {payment_info}...")
    payment_success = True  # In real case, integrate with a payment gateway

    if payment_success:
        # Record the order
        cursor.execute('''INSERT INTO orders (user_id, total_price, shipping_address, payment_status)
                          VALUES (?, ?, ?, ?)''', (user_id, total_price, shipping_address, 'Success'))
        order_id = cursor.lastrowid

        # Record the order items
        for item in cart_items:
            cursor.execute('''INSERT INTO order_items (order_id, product_id, quantity, price)
                              VALUES (?, ?, ?, ?)''', (order_id, item[0], item[3], item[2]))

        # Clear the cart
        cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()

        print(f"Order successfully placed! Order ID: {order_id}")
    else:
        print("Payment failed")

# Test the checkout function
checkout(1)

# Close the connection
conn.close()