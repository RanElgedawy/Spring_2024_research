import sqlite3
from contextlib import contextmanager

# Database setup and utilities
@contextmanager
def db_connection():
    conn = sqlite3.connect('ecommerce.db')
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()

def setup_database():
    with db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS carts")
        cursor.execute("DROP TABLE IF EXISTS orders")
        cursor.execute("DROP TABLE IF EXISTS order_items")
        cursor.execute("DROP TABLE IF EXISTS transactions")

        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                shipping_address TEXT,
                payment_method_token TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(product_id) REFERENCES products(product_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                shipping_address TEXT NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                PRIMARY KEY(order_id, product_id),
                FOREIGN KEY(order_id) REFERENCES orders(order_id),
                FOREIGN KEY(product_id) REFERENCES products(product_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(order_id) REFERENCES orders(order_id)
            )
        ''')
        conn.commit()

# Core checkout functionality
class CheckoutSystem:
    SHIPPING_FEE = 20.00

    def __init__(self, user_id):
        self.user_id = user_id
        self.cart_items = []
        self.shipping_address = ""
        self.total_amount = 0.0

    def retrieve_cart_items(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.product_id, p.name, c.quantity, p.price
                FROM carts c
                JOIN products p ON c.product_id = p.product_id
                WHERE c.user_id = ?
            ''', (self.user_id,))
            self.cart_items = cursor.fetchall()

    def retrieve_shipping_address(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT shipping_address FROM users WHERE user_id = ?
            ''', (self.user_id,))
            result = cursor.fetchone()
            self.shipping_address = result[0] if result else ""

    def calculate_total(self):
        subtotal = sum(item[2] * item[3] for item in self.cart_items)
        self.total_amount = subtotal + self.SHIPPING_FEE
        return self.total_amount

    def process_payment(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT payment_method_token FROM users WHERE user_id = ?
            ''', (self.user_id,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                raise ValueError("No valid payment method on file")
            
            # Simulate payment processing
            print(f"Processing payment of ${self.total_amount:.2f} using token: {result[0]}")
            return True  # Assume payment always succeeds for simulation

    def create_order(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            try:
                # Create order
                cursor.execute('''
                    INSERT INTO orders (user_id, total_amount, shipping_address)
                    VALUES (?, ?, ?)
                ''', (self.user_id, self.total_amount, self.shipping_address))
                order_id = cursor.lastrowid

                # Add order items
                for item in self.cart_items:
                    product_id, _, quantity, price = item
                    cursor.execute('''
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                        VALUES (?, ?, ?, ?)
                    ''', (order_id, product_id, quantity, price))

                # Record transaction
                cursor.execute('''
                    INSERT INTO transactions (order_id, amount, status)
                    VALUES (?, ?, ?)
                ''', (order_id, self.total_amount, 'success'))

                # Clear cart
                cursor.execute('DELETE FROM carts WHERE user_id = ?', (self.user_id,))
                
                conn.commit()
                return order_id
            except:
                conn.rollback()
                raise

    def checkout(self):
        self.retrieve_cart_items()
        if not self.cart_items:
            raise ValueError("Cannot checkout with empty cart")
        
        self.retrieve_shipping_address()
        if not self.shipping_address:
            raise ValueError("No shipping address found")
        
        total = self.calculate_total()
        if self.process_payment():
            order_id = self.create_order()
            return order_id
        return None

# Test utilities
def create_test_data():
    with db_connection() as conn:
        cursor = conn.cursor()
        
        # Test user
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, shipping_address, payment_method_token)
            VALUES (1, 'test_user', '123 Main St, Cityville', 'pm_test_123')
        ''')
        
        # Test products
        cursor.executemany('''
            INSERT OR IGNORE INTO products (product_id, name, price)
            VALUES (?, ?, ?)
        ''', [
            (101, 'Wireless Headphones', 199.99),
            (102, 'Smartwatch', 299.99),
            (103, 'Tablet', 499.99)
        ])
        
        # Test cart items
        cursor.execute('DELETE FROM carts WHERE user_id = 1')
        cursor.executemany('''
            INSERT INTO carts (user_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', [
            (1, 101, 2),
            (1, 103, 1)
        ])
        conn.commit()

def test_checkout():
    setup_database()
    create_test_data()
    
    print("Starting checkout test...")
    checkout_system = CheckoutSystem(1)
    
    try:
        order_id = checkout_system.checkout()
        print(f"Checkout successful! Order ID: {order_id}")
        
        # Verify results
        with db_connection() as conn:
            cursor = conn.cursor()
            
            # Check cart is empty
            cursor.execute('SELECT COUNT(*) FROM carts WHERE user_id = 1')
            cart_count = cursor.fetchone()[0]
            print(f"Items in cart after checkout: {cart_count}")
            
            # Check order exists
            cursor.execute('''
                SELECT o.total_amount, t.status 
                FROM orders o
                JOIN transactions t ON o.order_id = t.order_id
                WHERE o.order_id = ?
            ''', (order_id,))
            order_data = cursor.fetchone()
            print(f"Order total: ${order_data[0]:.2f}, Status: {order_data[1]}")
            
    except Exception as e:
        print(f"Checkout failed: {str(e)}")

if __name__ == "__main__":
    test_checkout()