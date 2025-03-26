import sqlite3
import uuid

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
            user_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            password TEXT,
            shipping_address TEXT,
            payment_info TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT,
            price REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            user_id TEXT,
            product_id TEXT,
            quantity INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id TEXT,
            total_amount REAL,
            shipping_address TEXT,
            order_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    conn.commit()
    conn.close()

def checkout(user_id):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Retrieve user information and cart items
    cursor.execute('SELECT shipping_address FROM users WHERE user_id = ?', (user_id,))
    shipping_address = cursor.fetchone()[0]

    cursor.execute('SELECT product_id, quantity, price FROM cart WHERE user_id = ?', (user_id,))
    cart_items = cursor.fetchall()

    # Calculate total amount (including shipping fee)
    total_amount = 20  # Shipping fee
    for item in cart_items:
        total_amount += item[2] * item[3]

    # Simulate payment processing (replace with actual payment gateway integration)
    payment_successful = True  # Replace with actual payment verification

    if payment_successful:
        # Create order
        order_id = str(uuid.uuid4())
        order_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO orders VALUES (?, ?, ?, ?, ?)', (order_id, user_id, total_amount, shipping_address, order_date))

        # Clear cart
        cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))

        conn.commit()
        print("Order placed successfully!")
    else:
        print("Payment failed.")

    conn.close()

# Example usage:
create_database()
checkout('user123')