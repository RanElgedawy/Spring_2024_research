import sqlite3
import json
from contextlib import contextmanager

DATABASE_NAME = 'ecommerce.db'

# Database connection helper
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Database initialization with sample tables
def initialize_db():
    with get_db_connection() as conn:
        # Create tables
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute("DROP TABLE IF EXISTS products")
        conn.execute("DROP TABLE IF EXISTS cart_items")
        conn.execute("DROP TABLE IF EXISTS transactions")

        conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        email TEXT UNIQUE,
                        street TEXT,
                        city TEXT,
                        state TEXT,
                        zip_code TEXT,
                        payment_method_id TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        price REAL)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS cart_items (
                        user_id INTEGER,
                        product_id INTEGER,
                        quantity INTEGER,
                        PRIMARY KEY (user_id, product_id),
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        FOREIGN KEY(product_id) REFERENCES products(id))''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_amount REAL,
                        shipping_address TEXT,
                        items TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id))''')

def checkout_order(user_id):
    SHIPPING_FEE = 20.0
    with get_db_connection() as conn:
        try:
            conn.execute("BEGIN TRANSACTION")

            # Get user shipping address
            user = conn.execute('''SELECT street, city, state, zip_code 
                                 FROM users WHERE id = ?''', (user_id,)).fetchone()
            if not user:
                raise ValueError("User not found")
            
            shipping_address = f"{user['street']}, {user['city']}, {user['state']} {user['zip']}"

            # Get cart items with product details
            cart_items = conn.execute('''SELECT p.id, p.name, p.price, c.quantity 
                                      FROM cart_items c
                                      JOIN products p ON c.product_id = p.id
                                      WHERE c.user_id = ?''', (user_id,)).fetchall()
            
            if not cart_items:
                raise ValueError("Cart is empty")

            # Calculate totals
            subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
            total = subtotal + SHIPPING_FEE

            # Process payment (simulated)
            # In real implementation, integrate with payment gateway here
            payment_method = conn.execute('''SELECT payment_method_id 
                                            FROM users WHERE id = ?''', (user_id,)).fetchone()
            if not payment_method['payment_method_id']:
                raise ValueError("No payment method on file")

            print(f"Simulating payment of ${total:.2f} using payment method {payment_method['payment_method_id']}")

            # Record transaction
            items_data = [dict(item) for item in cart_items]
            conn.execute('''INSERT INTO transactions 
                          (user_id, total_amount, shipping_address, items)
                          VALUES (?, ?, ?, ?)''',
                         (user_id, total, shipping_address, json.dumps(items_data)))

            # Clear cart
            conn.execute('DELETE FROM cart_items WHERE user_id = ?', (user_id,))

            conn.commit()
            print("Checkout successful!")
            return True

        except Exception as e:
            conn.rollback()
            print(f"Checkout failed: {str(e)}")
            return False

# Test functionality
def test_checkout():
    # Initialize test data
    with get_db_connection() as conn:
        # Create test user
        conn.execute('''INSERT OR IGNORE INTO users 
                      (id, email, street, city, state, zip_code, payment_method_id)
                      VALUES (1, 'test@example.com', '123 Main St', 
                              'Anytown', 'CA', '12345', 'pm_test123')''')
        
        # Create test products
        conn.execute('''INSERT OR IGNORE INTO products (id, name, price)
                      VALUES (1, 'Product A', 49.99), (2, 'Product B', 99.95)''')
        
        # Add items to cart
        conn.execute('''INSERT OR REPLACE INTO cart_items (user_id, product_id, quantity)
                      VALUES (1, 1, 2), (1, 2, 1)''')
        conn.commit()

    # Execute checkout
    print("Starting test checkout...")
    success = checkout_order(1)
    
    # Verify results
    with get_db_connection() as conn:
        if success:
            transaction = conn.execute('''SELECT * FROM transactions 
                                         WHERE user_id = 1''').fetchone()
            print("\nTransaction details:")
            print(f"ID: {transaction['id']}")
            print(f"Total: ${transaction['total_amount']:.2f}")
            print(f"Shipping to: {transaction['shipping_address']}")
            print("Items:")
            for item in json.loads(transaction['items']):
                print(f"- {item['name']} x{item['quantity']} @ ${item['price']:.2f}")

            cart_count = conn.execute('''SELECT COUNT(*) FROM cart_items 
                                       WHERE user_id = 1''').fetchone()[0]
            print(f"\nCart items after checkout: {cart_count}")

if __name__ == "__main__":
    initialize_db()
    test_checkout()