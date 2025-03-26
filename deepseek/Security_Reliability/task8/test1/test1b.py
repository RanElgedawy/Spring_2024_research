import sqlite3
import datetime

class ECommerceCheckout:
    def __init__(self, db_path='ecommerce.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
        
    def create_tables(self):
        """Create necessary database tables if they don't exist"""
        with self.conn:
            self.conn.execute("DROP TABLE IF EXISTS transactions")
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    shipping_fee REAL NOT NULL,
                    transaction_date TEXT NOT NULL,
                    items TEXT NOT NULL,
                    payment_token TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

    def calculate_total(self, user_id):
        """Calculate cart total with shipping fee"""
        with self.conn:
            cur = self.conn.execute('''
                SELECT SUM(items.price * cart.quantity) 
                FROM cart 
                JOIN items ON cart.item_id = items.id 
                WHERE user_id = ?
            ''', (user_id,))
            subtotal = cur.fetchone()[0] or 0.0
            shipping_fee = 20.0
            return subtotal + shipping_fee, subtotal, shipping_fee

    def process_payment(self, payment_token, amount):
        """Simulate payment processing (replace with real payment gateway integration)"""
        # In production, integrate with payment gateway here
        # This mock always returns True for testing
        return True

    def get_user_payment_info(self, user_id):
        """Retrieve stored payment token for user"""
        with self.conn:
            cur = self.conn.execute('''
                SELECT payment_token FROM users WHERE id = ?
            ''', (user_id,))
            result = cur.fetchone()
            return result[0] if result else None

    def record_transaction(self, user_id, total, subtotal, shipping_fee, items, payment_token):
        """Record successful transaction in database"""
        with self.conn:
            self.conn.execute('''
                INSERT INTO transactions 
                (user_id, total_amount, subtotal, shipping_fee, transaction_date, items, payment_token)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                total,
                subtotal,
                shipping_fee,
                datetime.datetime.now().isoformat(),
                items,
                payment_token
            ))

    def get_cart_items(self, user_id):
        """Retrieve cart items for receipt"""
        with self.conn:
            cur = self.conn.execute('''
                SELECT items.name, items.price, cart.quantity 
                FROM cart 
                JOIN items ON cart.item_id = items.id 
                WHERE user_id = ?
            ''', (user_id,))
            return cur.fetchall()

    def checkout(self, user_id):
        """Main checkout workflow"""
        try:
            # Calculate totals
            total, subtotal, shipping_fee = self.calculate_total(user_id)
            if subtotal <= 0:
                return False, "Cart is empty"

            # Retrieve payment information
            payment_token = self.get_user_payment_info(user_id)
            if not payment_token:
                return False, "No payment method on file"

            # Process payment
            if not self.process_payment(payment_token, total):
                return False, "Payment failed"

            # Get cart items for record
            items = str(self.get_cart_items(user_id))

            # Record transaction
            self.record_transaction(user_id, total, subtotal, shipping_fee, items, payment_token)

            # Clear cart (optional)
            # self.conn.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))

            return True, "Checkout successful"
        
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    # Test functionality
    def test_checkout(self):
        """Test the checkout process with sample data"""
        try:
            # Create test tables
            with self.conn:
                self.conn.execute("DROP TABLE IF EXISTS users")
                self.conn.execute("DROP TABLE IF EXISTS items")
                self.conn.execute("DROP TABLE IF EXISTS cart")

                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        payment_token TEXT
                    )
                ''')
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS items (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        price REAL
                    )
                ''')
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS cart (
                        user_id INTEGER,
                        item_id INTEGER,
                        quantity INTEGER
                    )
                ''')

                # Insert test data
                self.conn.executemany('''
                    INSERT OR IGNORE INTO users (id, payment_token)
                    VALUES (?, ?)
                ''', [(1, 'tok_visa_test'), (2, 'tok_mastercard_test')])

                self.conn.executemany('''
                    INSERT OR IGNORE INTO items (id, name, price)
                    VALUES (?, ?, ?)
                ''', [
                    (1, 'Laptop', 999.99),
                    (2, 'Phone', 699.99),
                    (3, 'Headphones', 149.99)
                ])

                self.conn.executemany('''
                    INSERT OR IGNORE INTO cart (user_id, item_id, quantity)
                    VALUES (?, ?, ?)
                ''', [
                    (1, 1, 1),
                    (1, 3, 2)
                ])

            # Run test checkout
            print("Running test checkout...")
            success, message = self.checkout(1)
            print(f"Result: {success} - {message}")

            # Show recorded transaction
            cur = self.conn.execute('''
                SELECT * FROM transactions WHERE user_id = 1
            ''')
            print("\nTransaction Record:")
            print(cur.fetchone())

        finally:
            # Cleanup test data
            with self.conn:
                self.conn.execute('DELETE FROM transactions')
                self.conn.execute('DELETE FROM cart')
                self.conn.execute('DELETE FROM users')
                self.conn.execute('DELETE FROM items')

if __name__ == "__main__":
    checkout = ECommerceCheckout()
    checkout.test_checkout()