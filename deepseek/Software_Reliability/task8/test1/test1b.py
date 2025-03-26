import sqlite3
from sqlite3 import Error
import datetime

class ECommerceCheckout:
    def __init__(self, db_file='ecommerce.db'):
        self.db_file = db_file
        self._create_tables()
        
    def _create_tables(self):
        """Create necessary database tables if they don't exist"""
        commands = [
            '''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                shipping_address TEXT,
                payment_info TEXT
            );''',
            
            '''CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );''',
            
            '''CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                shipping_address TEXT NOT NULL,
                order_date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );''',
            
            '''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            );'''
        ]
        
        conn = self._create_connection()
        try:
            c = conn.cursor()
            for command in commands:
                c.execute(command)
            conn.commit()
        except Error as e:
            print(e)
        finally:
            conn.close()

    def _create_connection(self):
        """Create a database connection"""
        try:
            return sqlite3.connect(self.db_file)
        except Error as e:
            print(e)
        return None

    def checkout(self, user_id):
        """Process checkout for a user"""
        conn = self._create_connection()
        try:
            # Retrieve cart items
            cart_items = self._get_cart_items(conn, user_id)
            if not cart_items:
                raise ValueError("Cart is empty")
            
            # Calculate total
            total = sum(item['price'] * item['quantity'] for item in cart_items)
            
            # Add shipping fee
            total += 20  # $20 shipping fee
            
            # Get shipping address
            shipping_address = self._get_shipping_address(conn, user_id)
            
            # Process payment (mock implementation)
            if not self._process_payment(conn, user_id, total):
                raise Exception("Payment processing failed")
            
            # Create order
            order_id = self._create_order(conn, user_id, total, shipping_address)
            
            # Record transaction
            self._create_transaction(conn, order_id, total)
            
            # Clear cart
            self._clear_cart(conn, user_id)
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Checkout failed: {str(e)}")
            return False
        finally:
            conn.close()

    def _get_cart_items(self, conn, user_id):
        """Retrieve current cart items"""
        c = conn.cursor()
        c.execute('''SELECT product_id, name, quantity, price 
                     FROM cart WHERE user_id = ?''', (user_id,))
        return [dict(row) for row in c.fetchall()]

    def _get_shipping_address(self, conn, user_id):
        """Get user's shipping address"""
        c = conn.cursor()
        c.execute('SELECT shipping_address FROM users WHERE id = ?', (user_id,))
        result = c.fetchone()
        if not result:
            raise ValueError("User not found or shipping address missing")
        return result[0]

    def _process_payment(self, conn, user_id, amount):
        """Mock payment processing"""
        # In real implementation, integrate with payment gateway
        # Here we just validate the user has payment info
        c = conn.cursor()
        c.execute('SELECT payment_info FROM users WHERE id = ?', (user_id,))
        payment_info = c.fetchone()
        return payment_info is not None  # Simplified check

    def _create_order(self, conn, user_id, total, shipping_address):
        """Create order record"""
        c = conn.cursor()
        order_date = datetime.datetime.now().isoformat()
        c.execute('''INSERT INTO orders 
                     (user_id, total_amount, shipping_address, order_date)
                     VALUES (?, ?, ?, ?)''',
                  (user_id, total, shipping_address, order_date))
        return c.lastrowid

    def _create_transaction(self, conn, order_id, amount):
        """Record transaction"""
        c = conn.cursor()
        transaction_date = datetime.datetime.now().isoformat()
        c.execute('''INSERT INTO transactions 
                     (order_id, amount, status, transaction_date)
                     VALUES (?, ?, ?, ?)''',
                  (order_id, amount, 'success', transaction_date))

    def _clear_cart(self, conn, user_id):
        """Clear user's cart after successful checkout"""
        c = conn.cursor()
        c.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))

# Test functionality
def test_checkout():
    # Initialize database
    db = ECommerceCheckout()
    
    # Create test user
    conn = sqlite3.connect('ecommerce.db')
    try:
        c = conn.cursor()
        # Insert test user
        c.execute('''INSERT INTO users 
                     (username, shipping_address, payment_info)
                     VALUES (?, ?, ?)''',
                  ('testuser', '123 Main St', 'mock_payment_info'))
        user_id = c.lastrowid
        
        # Add test items to cart
        c.executemany('''INSERT INTO cart 
                        (user_id, product_id, name, quantity, price)
                        VALUES (?, ?, ?, ?, ?)''',
                     [
                         (user_id, 1, 'Product A', 2, 15.99),
                         (user_id, 2, 'Product B', 1, 29.99)
                     ])
        conn.commit()
    finally:
        conn.close()
    
    # Perform checkout
    checkout_system = ECommerceCheckout()
    result = checkout_system.checkout(user_id)
    
    # Verify results
    conn = sqlite3.connect('ecommerce.db')
    try:
        c = conn.cursor()
        
        # Check orders
        c.execute('SELECT * FROM orders WHERE user_id = ?', (user_id,))
        order = c.fetchone()
        assert order is not None, "Order not created"
        assert order[2] == (2*15.99 + 29.99) + 20, "Incorrect total amount"
        
        # Check transactions
        c.execute('SELECT * FROM transactions WHERE order_id = ?', (order[0],))
        transaction = c.fetchone()
        assert transaction is not None, "Transaction not recorded"
        assert transaction[3] == 'success', "Transaction not successful"
        
        # Check cart clearance
        c.execute('SELECT COUNT(*) FROM cart WHERE user_id = ?', (user_id,))
        assert c.fetchone()[0] == 0, "Cart not cleared"
        
        print("All tests passed!")
    finally:
        conn.close()
        
if __name__ == '__main__':
    test_checkout()