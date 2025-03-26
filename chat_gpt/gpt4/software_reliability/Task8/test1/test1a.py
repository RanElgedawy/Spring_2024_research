import sqlite3

# Database setup function to create necessary tables
def setup_database():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS cart_items")
    c.execute("DROP TABLE IF EXISTS orders")
    
    # Create Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    shipping_address TEXT,
                    payment_info TEXT
                )''')

    # Create Cart Items table
    c.execute('''CREATE TABLE IF NOT EXISTS cart_items (
                    cart_item_id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    product_id INTEGER,
                    product_name TEXT,
                    quantity INTEGER,
                    price_per_unit REAL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )''')

    # Create Orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    total_price REAL,
                    shipping_fee REAL,
                    status TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )''')

    conn.commit()
    conn.close()

# Function to simulate the payment process (here we'll always return success)
def process_payment(user_payment_info, total_price):
    # Normally you'd integrate with a payment provider here
    # For testing, we'll simulate a success response
    print(f"Processing payment for {total_price} with payment info: {user_payment_info}")
    return True  # Assume payment is always successful

# Checkout function
def checkout(user_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    # Get user details
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    if not user:
        print("User not found!")
        return
    user_name, shipping_address, payment_info = user[1], user[2], user[3]

    # Get cart items for the user
    c.execute('SELECT * FROM cart_items WHERE user_id = ?', (user_id,))
    cart_items = c.fetchall()
    if not cart_items:
        print("Cart is empty!")
        return

    # Calculate total price
    total_price = sum(item[4] * item[5] for item in cart_items)
    shipping_fee = 20.00
    total_price_with_shipping = total_price + shipping_fee

    # Process payment
    if process_payment(payment_info, total_price_with_shipping):
        # Save the order if payment is successful
        c.execute('INSERT INTO orders (user_id, total_price, shipping_fee, status) VALUES (?, ?, ?, ?)',
                  (user_id, total_price_with_shipping, shipping_fee, 'Success'))
        order_id = c.lastrowid

        # Optionally, clear the user's cart
        c.execute('DELETE FROM cart_items WHERE user_id = ?', (user_id,))
        
        conn.commit()
        print(f"Order {order_id} placed successfully for {user_name}")
    else:
        print("Payment failed!")

    conn.close()

# Function to insert sample data for testing
def insert_sample_data():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    # Insert a sample user
    c.execute('''INSERT INTO users (name, shipping_address, payment_info) 
                 VALUES (?, ?, ?)''', 
                 ('John Doe', '123 Main St, Springfield', 'VISA_1234'))

    # Get user ID of the inserted user
    user_id = c.lastrowid

    # Insert some sample cart items for the user
    c.execute('''INSERT INTO cart_items (user_id, product_id, product_name, quantity, price_per_unit)
                 VALUES (?, ?, ?, ?, ?)''', (user_id, 1, 'Laptop', 1, 999.99))
    c.execute('''INSERT INTO cart_items (user_id, product_id, product_name, quantity, price_per_unit)
                 VALUES (?, ?, ?, ?, ?)''', (user_id, 2, 'Mouse', 2, 25.00))

    conn.commit()
    conn.close()
    print("Sample data inserted.")

# Running setup and test
if __name__ == '__main__':
    # Setup the database
    setup_database()

    # Insert sample data
    insert_sample_data()

    # Checkout for the user
    checkout(1)  # User ID 1
