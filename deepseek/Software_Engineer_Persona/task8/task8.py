import sqlite3
import datetime

# Database setup
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

cursor.executescript('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    shipping_address TEXT,
    payment_info TEXT,
    is_logged_in BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS cart (
    cart_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    total_amount REAL NOT NULL,
    shipping_address TEXT NOT NULL,
    payment_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    transaction_id TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price_at_purchase REAL NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(order_id),
    FOREIGN KEY(product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    user_id INTEGER,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
''')
conn.commit()

def check_authentication(user_id):
    """Check if user is logged in"""
    cursor.execute('''
    SELECT is_logged_in, payment_info FROM users WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    
    if not result:
        raise ValueError("User does not exist")
    
    return result[0], result[1]

def retrieve_cart_items(user_id):
    """Retrieve items in the user's cart with product details"""
    cursor.execute('''
    SELECT p.product_id, p.name, c.quantity, p.price
    FROM cart c
    JOIN products p ON c.product_id = p.product_id
    WHERE c.user_id = ?
    ''', (user_id,))
    return cursor.fetchall()

def calculate_total(cart_items):
    """Calculate order total including $20 shipping fee"""
    subtotal = sum(item[2] * item[3] for item in cart_items)
    return subtotal + 20  # $20 shipping fee

def process_payment(payment_info, amount):
    """Mock payment processing with transaction recording"""
    print(f"Processing payment of ${amount:.2f} using card: {payment_info[-4:]}")
    
    # Validate payment info
    if not payment_info or len(payment_info) != 16 or not payment_info.isdigit():
        print("Invalid payment information")
        return None
        
    # Generate mock transaction ID
    transaction_id = f"TX{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Record transaction
    try:
        cursor.execute('''
        INSERT INTO transactions (
            transaction_id, 
            user_id, 
            amount, 
            status, 
            transaction_date,
            payment_method
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            transaction_id,
            1,  # In real system, get user_id from context
            amount,
            'completed',
            datetime.datetime.now().isoformat(),
            f"card_{payment_info[-4:]}"
        ))
        conn.commit()
    except Exception as e:
        print(f"Failed to record transaction: {str(e)}")
        return None
    
    return transaction_id

def create_order(user_id, total, shipping_address, cart_items, transaction_id):
    """Create order record and associated order items"""
    try:
        cursor.execute('BEGIN TRANSACTION')
        
        # Create order record
        payment_date = datetime.datetime.now().isoformat()
        cursor.execute('''
        INSERT INTO orders (
            user_id, 
            total_amount, 
            shipping_address, 
            payment_date,
            status,
            transaction_id
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id, 
            total, 
            shipping_address, 
            payment_date,
            'paid',
            transaction_id
        ))
        order_id = cursor.lastrowid

        # Create order items
        for item in cart_items:
            product_id, _, quantity, price = item
            cursor.execute('''
            INSERT INTO order_items (
                order_id, 
                product_id, 
                quantity, 
                price_at_purchase
            ) VALUES (?, ?, ?, ?)
            ''', (order_id, product_id, quantity, price))

        # Clear cart
        cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Order creation failed: {str(e)}")
        conn.rollback()
        return False

def checkout(user_id):
    """Complete checkout process for a user"""
    try:
        # Authentication check
        is_logged_in, payment_info = check_authentication(user_id)
        if not is_logged_in:
            print("User not logged in")
            return False

        # Payment info check
        if not payment_info:
            print("No saved payment method found")
            return False

        # Retrieve cart items
        cart_items = retrieve_cart_items(user_id)
        if not cart_items:
            print("Cart is empty")
            return False

        # Calculate total with shipping
        total = calculate_total(cart_items)
        
        # Process payment
        transaction_id = process_payment(payment_info, total)
        if not transaction_id:
            print("Payment failed")
            return False

        # Get shipping address
        cursor.execute('''
        SELECT shipping_address FROM users WHERE user_id = ?
        ''', (user_id,))
        shipping_address = cursor.fetchone()[0]

        # Create order
        if create_order(user_id, total, shipping_address, cart_items, transaction_id):
            print("Order created successfully")
            return True
        return False
        
    except Exception as e:
        print(f"Checkout error: {str(e)}")
        return False

def test_checkout():
    """Test the checkout process with sample data"""
    cursor.executescript('''
    DELETE FROM users;
    DELETE FROM products;
    DELETE FROM cart;
    DELETE FROM orders;
    DELETE FROM order_items;
    DELETE FROM transactions;
    
    INSERT INTO users (user_id, username, shipping_address, payment_info, is_logged_in)
    VALUES 
        (1, 'test_user', '123 Main St, City, Country', '4111111111111111', 1),
        (2, 'logged_out_user', '456 Oak St', '5555555555554444', 0);
    
    INSERT INTO products (product_id, name, price)
    VALUES 
        (1, 'Laptop', 999.99),
        (2, 'Phone', 599.99);
    
    INSERT INTO cart (user_id, product_id, quantity)
    VALUES
        (1, 1, 1),
        (1, 2, 2);
    ''')
    conn.commit()
    
    print("--- Starting Checkout Test ---")
    result = checkout(1)
    print(f"\nCheckout result: {'Success' if result else 'Failure'}")
    
    # Display order status
    cursor.execute('''
    SELECT o.order_id, o.total_amount, o.status, t.transaction_id, t.status
    FROM orders o
    JOIN transactions t ON o.transaction_id = t.transaction_id
    WHERE o.user_id = 1
    ''')
    order = cursor.fetchone()
    print("\nOrder Status:")
    print(f"Order ID: {order[0]}")
    print(f"Total Amount: ${order[1]:.2f}")
    print(f"Order Status: {order[2]}")
    print(f"Transaction ID: {order[3]}")
    print(f"Transaction Status: {order[4]}")
    
    # Display inventory update
    cursor.execute('SELECT * FROM cart WHERE user_id = 1')
    print("\nRemaining Cart Items:", cursor.fetchall())

if __name__ == '__main__':
    test_checkout()
    conn.close()