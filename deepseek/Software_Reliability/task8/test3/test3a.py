import sqlite3
from datetime import datetime

class ECommerceDB:
    def __init__(self, db_name='ecommerce.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS cart")
        cursor.execute("DROP TABLE IF EXISTS orders")
        cursor.execute("DROP TABLE IF EXISTS order_items")
        cursor.execute("DROP TABLE IF EXISTS transactions")

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                shipping_address TEXT NOT NULL,
                payment_method TEXT NOT NULL
            )
        ''')
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        # Create cart table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(product_id) REFERENCES products(product_id)
            )
        ''')
        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                shipping_address TEXT NOT NULL,
                order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # Create order_items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price_at_purchase REAL NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(order_id),
                FOREIGN KEY(product_id) REFERENCES products(product_id)
            )
        ''')
        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(order_id)
            )
        ''')
        self.conn.commit()

    def add_user(self, user_id, username, shipping_address, payment_method):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO users (id, username, shipping_address, payment_method)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, shipping_address, payment_method))
        self.conn.commit()

    def add_product(self, product_id, name, price):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO products (product_id, name, price)
            VALUES (?, ?, ?)
        ''', (product_id, name, price))
        self.conn.commit()

    def add_to_cart(self, user_id, product_id, quantity):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO cart (user_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', (user_id, product_id, quantity))
        self.conn.commit()

    def get_cart_items(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT p.product_id, p.name, c.quantity, p.price
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = ?
        ''', (user_id,))
        return [{
            'product_id': row[0],
            'name': row[1],
            'quantity': row[2],
            'price': row[3]
        } for row in cursor.fetchall()]

    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'shipping_address': row[2],
                'payment_method': row[3]
            }
        return None

    def process_payment(self, payment_method, amount):
        # Simulated payment processing
        # In real implementation, integrate with payment gateway
        return True  # Always succeeds for demonstration

    def checkout(self, user_id):
        try:
            with self.conn:
                cart_items = self.get_cart_items(user_id)
                if not cart_items:
                    return False, "Cart is empty"

                user = self.get_user(user_id)
                if not user:
                    return False, "User not found"

                # Calculate totals
                subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
                shipping_fee = 20.0
                total = subtotal + shipping_fee

                # Process payment
                if not self.process_payment(user['payment_method'], total):
                    return False, "Payment failed"

                # Create order
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO orders (user_id, total_amount, shipping_address)
                    VALUES (?, ?, ?)
                ''', (user_id, total, user['shipping_address']))
                order_id = cursor.lastrowid

                # Add order items
                for item in cart_items:
                    cursor.execute('''
                        INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase)
                        VALUES (?, ?, ?, ?)
                    ''', (order_id, item['product_id'], item['quantity'], item['price']))

                # Record transaction
                cursor.execute('''
                    INSERT INTO transactions (order_id, amount, payment_method, status)
                    VALUES (?, ?, ?, ?)
                ''', (order_id, total, user['payment_method'], 'success'))

                # Clear cart
                cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))

                return True, "Checkout successful"
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"

    def clear_all_data(self):
        """Utility method for testing"""
        cursor = self.conn.cursor()
        tables = ['users', 'products', 'cart', 'orders', 'order_items', 'transactions']
        for table in tables:
            cursor.execute(f'DELETE FROM {table}')
        self.conn.commit()

# Test function
def test_checkout():
    db = ECommerceDB()
    db.clear_all_data()  # Start fresh
    
    # Setup test data
    user_id = 1
    db.add_user(user_id, 'test_user', '123 Main St, City', 'VISA-1234')
    db.add_product(1, 'Laptop', 999.99)
    db.add_product(2, 'Mouse', 29.99)
    db.add_to_cart(user_id, 1, 2)  # 2 laptops
    db.add_to_cart(user_id, 2, 1)  # 1 mouse

    # Perform checkout
    success, message = db.checkout(user_id)
    print(f"Checkout result: {success}, Message: {message}")

    # Verify results
    if success:
        cursor = db.conn.cursor()
        # Verify orders
        cursor.execute('SELECT * FROM orders WHERE user_id = ?', (user_id,))
        order = cursor.fetchone()
        print("\nOrder details:")
        print(f"Order ID: {order[0]}, Total: ${order[2]:.2f}, Shipping Address: {order[3]}")

        # Verify order items
        cursor.execute('SELECT * FROM order_items WHERE order_id = ?', (order[0],))
        print("\nOrder items:")
        for item in cursor.fetchall():
            print(f"Product ID: {item[1]}, Quantity: {item[2]}, Price: ${item[3]:.2f}")

        # Verify transaction
        cursor.execute('SELECT * FROM transactions WHERE order_id = ?', (order[0],))
        transaction = cursor.fetchone()
        print("\nTransaction details:")
        print(f"Amount: ${transaction[2]:.2f}, Payment Method: {transaction[3]}, Status: {transaction[5]}")

        # Verify empty cart
        cart_items = db.get_cart_items(user_id)
        print(f"\nCart items after checkout: {len(cart_items)}")

if __name__ == '__main__':
    test_checkout()