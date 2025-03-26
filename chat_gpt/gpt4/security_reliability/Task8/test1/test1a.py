import sqlite3
from datetime import datetime

# Mock Payment Processor
class PaymentProcessor:
    def __init__(self, card_number, expiration_date, cvv, total_amount):
        self.card_number = card_number
        self.expiration_date = expiration_date
        self.cvv = cvv
        self.total_amount = total_amount

    def process_payment(self):
        # In a real-world scenario, use a payment gateway like Stripe, PayPal, etc.
        # For this mock, we just return True assuming the payment is successful
        return True

# Checkout system for e-commerce
class CheckoutSystem:
    SHIPPING_FEE = 20  # Flat shipping fee

    def __init__(self, db_name='ecommerce.db'):
        self.db_name = db_name
        self._create_tables()

    def _create_tables(self):
        # Connect to database and create tables if they don't exist
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Table to store users
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            shipping_address TEXT,
            card_number TEXT,
            card_expiration TEXT,
            card_cvv TEXT
        )''')

        # Table to store items
        cursor.execute("DROP TABLE IF EXISTS items")
        cursor.execute('''CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL
        )''')

        # Table to store cart (linking users and items)
        cursor.execute("DROP TABLE IF EXISTS cart")
        cursor.execute('''CREATE TABLE IF NOT EXISTS cart (
            user_id INTEGER,
            item_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(item_id) REFERENCES items(id)
        )''')

        # Table to store transactions
        cursor.execute("DROP TABLE IF EXISTS transactions")
        cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            total_amount REAL,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')

        conn.commit()
        conn.close()

    def get_cart_total(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''SELECT SUM(i.price * c.quantity) FROM cart c
                          JOIN items i ON c.item_id = i.id
                          WHERE c.user_id = ?''', (user_id,))
        total = cursor.fetchone()[0] or 0
        conn.close()
        return total

    def checkout(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Fetch user payment and shipping information
        cursor.execute('SELECT card_number, card_expiration, card_cvv, shipping_address FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            conn.close()
            raise Exception("User not found")

        card_number, card_expiration, card_cvv, shipping_address = user_data

        # Calculate cart total and apply shipping fee
        cart_total = self.get_cart_total(user_id)
        total_with_shipping = cart_total + self.SHIPPING_FEE

        # Process payment (mock)
        payment_processor = PaymentProcessor(card_number, card_expiration, card_cvv, total_with_shipping)
        if payment_processor.process_payment():
            # Record the transaction
            cursor.execute('INSERT INTO transactions (user_id, total_amount, date) VALUES (?, ?, ?)',
                           (user_id, total_with_shipping, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()

            print(f"Transaction successful for user {user_id}. Total: ${total_with_shipping}")

            # Clear the cart
            cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
            conn.commit()
        else:
            print("Payment failed, transaction aborted.")

        conn.close()

# Test function
def test_checkout_system():
    checkout_system = CheckoutSystem()

    # Adding a mock user and items
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Add a test user
    cursor.execute('''INSERT OR IGNORE INTO users (id, name, email, shipping_address, card_number, card_expiration, card_cvv)
                      VALUES (1, 'John Doe', 'johndoe@example.com', '123 Test St', '1234567812345678', '12/25', '123')''')

    # Add some test items
    cursor.execute('INSERT OR IGNORE INTO items (id, name, price) VALUES (1, "Laptop", 1000)')
    cursor.execute('INSERT OR IGNORE INTO items (id, name, price) VALUES (2, "Mouse", 25)')

    # Add items to the cart
    cursor.execute('INSERT OR IGNORE INTO cart (user_id, item_id, quantity) VALUES (1, 1, 1)')
    cursor.execute('INSERT OR IGNORE INTO cart (user_id, item_id, quantity) VALUES (1, 2, 2)')

    conn.commit()
    conn.close()

    # Perform checkout for the user with ID 1
    checkout_system.checkout(1)

# Run the test
if __name__ == "__main__":
    test_checkout_system()
