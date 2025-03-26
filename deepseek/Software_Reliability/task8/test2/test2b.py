import sqlite3
from datetime import datetime

def initialize_database():
    conn = sqlite3.connect('ecommerce.db')
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
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_info TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            shipping_address TEXT NOT NULL,
            order_date DATETIME NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            transaction_date DATETIME NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    ''')

    conn.commit()
    conn.close()

def process_payment(user_id, amount):
    """Mock payment processing function"""
    # In real implementation, use user's payment_info to process payment
    # For testing purposes, always return True
    return True

def checkout(user_id):
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        conn.execute('BEGIN TRANSACTION')

        # Retrieve cart items with product details
        cursor.execute('''
            SELECT products.id, products.name, carts.quantity, products.price
            FROM carts
            JOIN products ON carts.product_id = products.id
            WHERE carts.user_id = ?
        ''', (user_id,))
        
        cart_items = cursor.fetchall()
        if not cart_items:
            print("Cart is empty")
            return False

        # Calculate total amount
        subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
        shipping_fee = 20.0
        total_amount = subtotal + shipping_fee

        # Retrieve shipping address
        cursor.execute('''
            SELECT shipping_address FROM users WHERE id = ?
        ''', (user_id,))
        user = cursor.fetchone()
        if not user:
            print("User not found")
            return False
        shipping_address = user['shipping_address']

        # Process payment
        if not process_payment(user_id, total_amount):
            print("Payment processing failed")
            conn.rollback()
            return False

        # Create order record
        order_date = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO orders (user_id, total_amount, shipping_address, order_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, total_amount, shipping_address, order_date))
        order_id = cursor.lastrowid

        # Create order items
        for item in cart_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['id'], item['quantity'], item['price']))

        # Create transaction record
        transaction_date = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO transactions (order_id, amount, status, transaction_date)
            VALUES (?, ?, ?, ?)
        ''', (order_id, total_amount, 'success', transaction_date))

        # Clear the cart
        cursor.execute('DELETE FROM carts WHERE user_id = ?', (user_id,))

        conn.commit()
        print("Checkout completed successfully")
        return True

    except Exception as e:
        conn.rollback()
        print(f"Error during checkout: {str(e)}")
        return False
    finally:
        conn.close()

def test_checkout():
    # Initialize database
    initialize_database()
    
    # Create test data
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute('DELETE FROM users')
    cursor.execute('DELETE FROM products')
    cursor.execute('DELETE FROM carts')
    cursor.execute('DELETE FROM orders')
    cursor.execute('DELETE FROM order_items')
    cursor.execute('DELETE FROM transactions')

    # Create test user
    cursor.execute('''
        INSERT INTO users (username, shipping_address, payment_info)
        VALUES (?, ?, ?)
    ''', ('testuser', '123 Main St, Test City', 'mock_payment_info'))
    user_id = cursor.lastrowid

    # Create test products
    products = [
        ('Product A', 49.99),
        ('Product B', 99.99)
    ]
    product_ids = []
    for name, price in products:
        cursor.execute('INSERT INTO products (name, price) VALUES (?, ?)', (name, price))
        product_ids.append(cursor.lastrowid)

    # Add items to cart
    cart_items = [
        (user_id, product_ids[0], 2),
        (user_id, product_ids[1], 1)
    ]
    for item in cart_items:
        cursor.execute('INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)', item)

    conn.commit()
    conn.close()

    # Execute checkout
    print("\nStarting checkout process...")
    result = checkout(user_id)
    assert result is True, "Checkout failed"

    # Verify results
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Check orders
    cursor.execute('SELECT * FROM orders WHERE user_id = ?', (user_id,))
    order = cursor.fetchone()
    assert order is not None, "No order created"
    
    expected_total = (2 * 49.99) + (1 * 99.99) + 20.0
    assert abs(order[2] - expected_total) < 0.01, "Incorrect total amount"

    # Check order items
    cursor.execute('SELECT COUNT(*) FROM order_items WHERE order_id = ?', (order[0],))
    assert cursor.fetchone()[0] == 2, "Incorrect number of order items"

    # Check transaction
    cursor.execute('SELECT * FROM transactions WHERE order_id = ?', (order[0],))
    transaction = cursor.fetchone()
    assert transaction is not None, "No transaction created"
    assert transaction[3] == 'success', "Transaction not marked as successful"

    # Check cart clearance
    cursor.execute('SELECT COUNT(*) FROM carts WHERE user_id = ?', (user_id,))
    assert cursor.fetchone()[0] == 0, "Cart not cleared"

    conn.close()
    print("All tests passed!")

if __name__ == '__main__':
    initialize_database()
    test_checkout()