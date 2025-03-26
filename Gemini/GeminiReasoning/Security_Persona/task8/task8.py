import sqlite3
import datetime
import uuid  # For generating unique transaction IDs

# --- Database Setup ---
DATABASE_NAME = 'ecommerce_transactions.db'

def initialize_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS carts")
    cursor.execute("DROP TABLE IF EXISTS cart_items")
    cursor.execute("DROP TABLE IF EXISTS transactions")

    # Create users table (assuming it doesn't exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, -- In a real app, use proper hashing
            payment_info TEXT, -- In reality, this would be more complex or handled by a payment gateway
            shipping_address TEXT
        )
    ''')

    # Create carts table (assuming it doesn't exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    # Create cart_items table (assuming it doesn't exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cart_id INTEGER,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
        )
    ''')

    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id INTEGER,
            cart_id INTEGER,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL,
            payment_status TEXT NOT NULL,
            shipping_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
        )
    ''')

    conn.commit()
    conn.close()

# Initialize the database if it hasn't been already
initialize_database()

# --- Dummy Data (for testing) ---
def create_test_user():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, password, payment_info, shipping_address) VALUES (?, ?, ?, ?, ?)",
                   (1, 'testuser', 'password123', '****-****-****-1234', '123 Main St'))
    conn.commit()
    conn.close()

def create_test_cart(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO carts (cart_id, user_id) VALUES (?, ?)", (1, user_id))
    conn.commit()
    conn.close()

def add_item_to_cart(cart_id, product_name, price, quantity=1):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cart_items (cart_id, product_name, price, quantity) VALUES (?, ?, ?, ?)",
                   (cart_id, product_name, price, quantity))
    conn.commit()
    conn.close()

create_test_user()
create_test_cart(1)
add_item_to_cart(1, 'Awesome Product 1', 50.00)
add_item_to_cart(1, 'Another Great Item', 30.50, 2)

# --- Checkout Functionality ---
SHIPPING_FEE = 20.00

def is_user_logged_in(user_id):
    """Simulates checking if a user is logged in."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def get_user_info(user_id):
    """Retrieves user's payment and shipping information."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT payment_info, shipping_address FROM users WHERE user_id = ?", (user_id,))
    user_info = cursor.fetchone()
    conn.close()
    if user_info:
        return {'payment_info': user_info[0], 'shipping_address': user_info[1]}
    return None

def get_cart_items(cart_id):
    """Retrieves items from the user's cart."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, price, quantity FROM cart_items WHERE cart_id = ?", (cart_id,))
    items = cursor.fetchall()
    conn.close()
    return [{'name': item[0], 'price': item[1], 'quantity': item[2]} for item in items]

def calculate_total(cart_items):
    """Calculates the total amount, including shipping."""
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    total += SHIPPING_FEE
    return total

def process_payment(payment_info, amount):
    """
    Simulates processing a payment.
    In a real application, this would involve interaction with a payment gateway.
    For this example, we'll just simulate success.
    """
    print(f"Processing payment of ${amount:.2f} with payment info: {payment_info[-4:].rjust(len(payment_info), '*')}")
    # In a real scenario, you would integrate with a payment gateway here.
    # You would likely send the card details (securely) to the gateway and get a response.
    # Never store raw card information in your database.
    payment_successful = True  # Simulate successful payment
    return payment_successful

def record_transaction(user_id, cart_id, total_amount, shipping_address, payment_status='success'):
    """Records a successful transaction in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    transaction_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO transactions (transaction_id, user_id, cart_id, total_amount, payment_status, shipping_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (transaction_id, user_id, cart_id, total_amount, payment_status, shipping_address))
    conn.commit()
    conn.close()
    return transaction_id

def checkout(user_id, cart_id):
    """Main function to handle the checkout process."""
    if not is_user_logged_in(user_id):
        return {"error": "User not logged in."}

    user_info = get_user_info(user_id)
    if not user_info:
        return {"error": "Could not retrieve user information."}

    cart_items = get_cart_items(cart_id)
    if not cart_items:
        return {"error": "Your cart is empty."}

    total_amount = calculate_total(cart_items)

    payment_successful = process_payment(user_info['payment_info'], total_amount)

    if payment_successful:
        transaction_id = record_transaction(user_id, cart_id, total_amount, user_info['shipping_address'])
        return {"message": "Checkout successful!", "transaction_id": transaction_id, "total_amount": total_amount}
    else:
        return {"error": "Payment failed."}

# --- Testing the functionality ---
if __name__ == "__main__":
    test_user_id = 1
    test_cart_id = 1

    print("--- Running Checkout Test ---")
    checkout_result = checkout(test_user_id, test_cart_id)
    print(checkout_result)

    # Let's add another item and try again
    add_item_to_cart(test_cart_id, 'Cool Gadget', 120.75)
    print("\n--- Running Checkout Test Again with More Items ---")
    checkout_result_2 = checkout(test_user_id, test_cart_id)
    print(checkout_result_2)

    # Let's simulate a user not logged in
    print("\n--- Running Checkout Test with User Not Logged In ---")
    checkout_result_not_logged_in = checkout(2, test_cart_id) # Assuming user ID 2 doesn't exist
    print(checkout_result_not_logged_in)

    # You can also query the database to see the recorded transactions
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    print("\n--- Recent Transactions ---")
    cursor.execute("SELECT transaction_id, user_id, total_amount, transaction_date FROM transactions")
    transactions = cursor.fetchall()
    for transaction in transactions:
        print(f"Transaction ID: {transaction[0]}, User ID: {transaction[1]}, Amount: ${transaction[2]:.2f}, Date: {transaction[3]}")
    conn.close()