import sqlite3
from contextlib import contextmanager

DATABASE_NAME = 'ecommerce.db'

# ====================
# Database Setup
# ====================
def setup_database():
    with db_connection() as conn:
        # Create Users Table

        conn.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY,
                     username TEXT UNIQUE,
                     email TEXT,
                     shipping_address TEXT,
                     payment_method TEXT)''')

        # Create Cart Table
        conn.execute('''CREATE TABLE IF NOT EXISTS cart
                     (user_id INTEGER,
                     product_id INTEGER,
                     product_name TEXT,
                     quantity INTEGER,
                     price REAL,
                     FOREIGN KEY(user_id) REFERENCES users(id))''')

        # Create Orders Table
        conn.execute('''CREATE TABLE IF NOT EXISTS orders
                     (order_id INTEGER PRIMARY KEY,
                     user_id INTEGER,
                     total_amount REAL,
                     shipping_address TEXT,
                     transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     FOREIGN KEY(user_id) REFERENCES users(id))''')

        # Create Order Items Table
        conn.execute('''CREATE TABLE IF NOT EXISTS order_items
                     (order_id INTEGER,
                     product_id INTEGER,
                     product_name TEXT,
                     quantity INTEGER,
                     price REAL,
                     FOREIGN KEY(order_id) REFERENCES orders(order_id))''')

# ====================
# Database Utilities
# ====================
@contextmanager
def db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.execute("PRAGMA foreign_keys = 1")  # Enable foreign key constraints
    try:
        yield conn
    finally:
        conn.close()

# ====================
# Checkout Functions
# ====================
def get_cart_items(user_id):
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT product_id, product_name, quantity, price 
                        FROM cart WHERE user_id = ?''', (user_id,))
        return cursor.fetchall()

def get_user_shipping(user_id):
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT shipping_address FROM users WHERE id = ?''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def calculate_total(cart_items):
    subtotal = sum(item[2] * item[3] for item in cart_items)  # quantity * price
    shipping_fee = 20.00
    return subtotal + shipping_fee

def process_payment(user_id, amount):
    # In real implementation, integrate with payment gateway
    # For simulation, just check if user has payment method
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT payment_method FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        return result is not None and result[0] is not None

def create_order(user_id, total, shipping_address, cart_items):
    with db_connection() as conn:
        try:
            # Create order record
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO orders 
                          (user_id, total_amount, shipping_address)
                          VALUES (?, ?, ?)''',
                          (user_id, total, shipping_address))
            
            order_id = cursor.lastrowid
            
            # Create order items
            for item in cart_items:
                cursor.execute('''INSERT INTO order_items 
                                (order_id, product_id, product_name, quantity, price)
                                VALUES (?, ?, ?, ?, ?)''',
                             (order_id, item[0], item[1], item[2], item[3]))
            
            # Clear cart
            cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
            
            conn.commit()
            return order_id
        except sqlite3.Error as e:
            conn.rollback()
            raise e

def checkout(user_id):
    try:
        # Retrieve cart items
        cart_items = get_cart_items(user_id)
        if not cart_items:
            raise ValueError("Cart is empty")
        
        # Get shipping address
        shipping_address = get_user_shipping(user_id)
        if not shipping_address:
            raise ValueError("Shipping address not found")
        
        # Calculate total
        total = calculate_total(cart_items)
        
        # Process payment
        if not process_payment(user_id, total):
            raise ValueError("Payment processing failed")
        
        # Create order
        order_id = create_order(user_id, total, shipping_address, cart_items)
        
        return {
            'success': True,
            'order_id': order_id,
            'total': total,
            'shipping_address': shipping_address
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ====================
# Test Utilities
# ====================
def create_test_user():
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users 
                       (username, email, shipping_address, payment_method)
                       VALUES (?, ?, ?, ?)''',
                    ('testuser', 'test@example.com', 
                     '123 Main St, City, Country', 'visa-xxxx'))
        return cursor.lastrowid

def add_test_cart_items(user_id):
    with db_connection() as conn:
        cursor = conn.cursor()
        # Add sample products
        cursor.executemany('''INSERT INTO cart 
                           (user_id, product_id, product_name, quantity, price)
                           VALUES (?, ?, ?, ?, ?)''',
                        [(user_id, 1, 'Product A', 2, 25.99),
                         (user_id, 2, 'Product B', 1, 49.99)])
        conn.commit()

def test_checkout():
    print("=== Starting Test ===")
    
    # Setup test environment
    setup_database()
    user_id = create_test_user()
    add_test_cart_items(user_id)
    
    # Perform checkout
    result = checkout(user_id)
    
    if result['success']:
        print(f"Checkout successful! Order ID: {result['order_id']}")
        print(f"Total charged: ${result['total']:.2f}")
        print(f"Shipping to: {result['shipping_address']}")
        
        # Verify database records
        with db_connection() as conn:
            cursor = conn.cursor()
            
            # Check orders
            cursor.execute('SELECT * FROM orders WHERE user_id = ?', (user_id,))
            order = cursor.fetchone()
            print("\nOrder Record:", order)
            
            # Check order items
            cursor.execute('SELECT * FROM order_items WHERE order_id = ?', (order[0],))
            items = cursor.fetchall()
            print("Order Items:", items)
            
            # Check cart clearance
            cursor.execute('SELECT COUNT(*) FROM cart WHERE user_id = ?', (user_id,))
            cart_count = cursor.fetchone()[0]
            print("Remaining cart items:", cart_count)
    else:
        print("Checkout failed:", result['error'])
    
    print("=== Test Complete ===")

if __name__ == '__main__':
    test_checkout()