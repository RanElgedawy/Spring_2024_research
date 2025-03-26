import sqlite3
import datetime

def create_database():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS orders")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            shipping_address TEXT,
            payment_info TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_date TEXT,
            total_amount REAL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    conn.commit()
    conn.close()

def checkout(user_id):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Retrieve user's shipping address and payment information
    cursor.execute('SELECT shipping_address, payment_info FROM users WHERE user_id = ?', (user_id,))
    user_info = cursor.fetchone()
    shipping_address, payment_info = user_info

    # Retrieve items from the user's cart
    cursor.execute('SELECT products.name, cart.quantity, products.price FROM cart INNER JOIN products ON cart.product_id = products.product_id WHERE cart.user_id = ?', (user_id,))
    cart_items = cursor.fetchall()

    # Calculate total cost, including shipping fee
    total_cost = 20  # Shipping fee
    for item in cart_items:
        total_cost += item[1] * item[2]

    # Simulate payment processing (replace with actual payment gateway)
    if simulate_payment(payment_info, total_cost):
        # Submit the order
        order_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO orders (user_id, order_date, total_amount) VALUES (?, ?, ?)', (user_id, order_date, total_cost))
        conn.commit()
        print('Order placed successfully!')
    else:
        print('Payment failed.')

    conn.close()

def simulate_payment(payment_info, amount):
    # Replace this with actual payment processing logic
    # For now, let's simulate a successful payment
    return True

# Example usage:
create_database()
checkout(1)  # Replace 1 with the actual user ID