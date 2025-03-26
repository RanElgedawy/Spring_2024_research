import sqlite3
import random
import time
from datetime import datetime

# --- Helper Functions ---

def get_user_info(user_id):
    """
    Simulates fetching a user's payment and shipping info from an existing user account.
    In production, this would pull from a secure user database.
    """
    # In a real system, payment info (e.g., card token) should be stored securely.
    # Never store raw card details. Here we simulate with placeholder data.
    return {
        "user_id": user_id,
        "name": "John Doe",
        "card_token": "secure_token_ABC123",  # placeholder token from a PCI-compliant payment system
        "shipping_address": "123 Main Street, City, Country"
    }

def process_payment(payment_info, amount):
    """
    Simulates processing a payment.
    In real life, this would call a payment gateway API.
    The function returns True if payment is successful.
    """
    # Do not log or expose sensitive payment details.
    # Here, we simulate success 80% of the time.
    success = random.random() < 0.8
    print(f"Processing payment for user {payment_info['user_id']} for amount ${amount:.2f} ...")
    time.sleep(1)  # simulate network delay
    return success

def create_transactions_table(db_conn):
    """
    Creates the transactions table if it does not exist.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        amount REAL,
        shipping_fee REAL,
        total REAL,
        transaction_time TEXT
    );
    """
    with db_conn:
        db_conn.execute("DROP TABLE IF EXISTS transactions")
        db_conn.execute(create_table_sql)
    print("Transactions table is ready.")

def record_transaction(db_conn, user_id, amount, shipping_fee, total):
    """
    Records a successful transaction in the database.
    """
    insert_sql = """
    INSERT INTO transactions (user_id, amount, shipping_fee, total, transaction_time)
    VALUES (?, ?, ?, ?, ?);
    """
    transaction_time = datetime.utcnow().isoformat()
    with db_conn:
        db_conn.execute(insert_sql, (user_id, amount, shipping_fee, total, transaction_time))
    print(f"Transaction recorded for user {user_id} at {transaction_time}.")

# --- Main Checkout Function ---

def checkout(user_id, cart_items, db_conn):
    """
    Processes checkout for a logged-in user.
    
    Parameters:
      user_id: Identifier for the user.
      cart_items: List of dictionaries with 'item_id' and 'price' keys.
      db_conn: Active SQLite database connection.
      
    Steps:
      1. Retrieve user information (payment and shipping info).
      2. Calculate total amount (items' cost + $20 shipping fee).
      3. Process payment.
      4. If successful, record the transaction in the database.
    """
    # Retrieve user info securely
    user_info = get_user_info(user_id)
    
    # Calculate subtotal
    subtotal = sum(item['price'] for item in cart_items)
    shipping_fee = 20.00
    total = subtotal + shipping_fee
    
    print(f"User {user_id} checkout: subtotal ${subtotal:.2f} + shipping fee ${shipping_fee:.2f} = total ${total:.2f}")
    
    # Process the payment securely
    if process_payment(user_info, total):
        print("Payment successful!")
        record_transaction(db_conn, user_id, subtotal, shipping_fee, total)
    else:
        print("Payment failed. Please try again.")

# --- Test Functionality ---

def main():
    # Create a test database in memory (for persistent testing, replace ':memory:' with a filename)
    db_conn = sqlite3.connect(':memory:')
    create_transactions_table(db_conn)
    
    # Example cart for testing: list of items with item_id and price
    cart_items = [
        {"item_id": "item101", "price": 50.00},
        {"item_id": "item102", "price": 30.00},
        {"item_id": "item103", "price": 20.00}
    ]
    
    # Simulated user id (in real use, from authentication context)
    user_id = "user123"
    
    # Execute checkout process
    checkout(user_id, cart_items, db_conn)
    
    # For testing: retrieve and display recorded transactions
    print("\nRecorded Transactions:")
    cursor = db_conn.execute("SELECT * FROM transactions;")
    for row in cursor.fetchall():
        print(row)
    
    # Close the database connection
    db_conn.close()

if __name__ == '__main__':
    main()
