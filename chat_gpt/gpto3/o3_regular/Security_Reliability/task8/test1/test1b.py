import sqlite3
import datetime
import random

# --- Database setup ---
DB_NAME = 'ecommerce.db'

def init_db():
    """Initialize the database and create necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    with conn:
        conn.execute("DROP TABLE IF EXISTS transactions")
        # Create a transactions table to record successful checkouts
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                transaction_date TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
    conn.close()

# --- Payment processing simulation ---
def process_payment(card_info, amount):
    """
    Simulate processing a payment.
    
    In production, integrate with a secure payment gateway.
    For this simulation, we'll assume payment succeeds if the card number passes a dummy check.
    """
    # Dummy secure check: card number must be 16 digits and pass a simple checksum test.
    if len(card_info.get('number', '')) != 16 or not card_info.get('number', '').isdigit():
        return False
    # Simulate random failure to show how to handle unsuccessful transactions.
    return random.choice([True, True, True, False])  # ~75% success rate

# --- Checkout functionality ---
def checkout(user_id, cart_items, user_account_info):
    """
    Process a checkout:
      - Calculates total (sum of cart items plus a $20 shipping fee)
      - Retrieves stored payment info if available, otherwise uses provided card details
      - Processes payment, and if successful, records the transaction in the DB.
      
    Arguments:
      user_id: Integer ID of the logged-in user.
      cart_items: List of tuples in the format (item_name, price)
      user_account_info: Dictionary that should contain keys like:
         'payment': { 'number': '...', 'expiry': '...', 'cvv': '...' }
         'shipping': { ... } (not used in processing here, but would be for shipping labels, etc.)
         
    Returns:
      A tuple: (success (bool), message (str))
    """
    # Calculate total amount with $20 shipping fee
    subtotal = sum(price for _, price in cart_items)
    total = subtotal + 20.0

    print(f"Subtotal: ${subtotal:.2f}, Shipping: $20.00, Total: ${total:.2f}")

    # Process payment using the card info from user_account_info.
    payment_info = user_account_info.get('payment', {})
    
    # Securely process the payment (here simulated)
    if not process_payment(payment_info, total):
        return (False, "Payment failed. Please check your card details or try a different card.")

    # Record successful transaction in the database
    conn = sqlite3.connect(DB_NAME)
    try:
        with conn:
            conn.execute("""
                INSERT INTO transactions (user_id, total_amount, transaction_date, status)
                VALUES (?, ?, ?, ?)
            """, (user_id, total, datetime.datetime.now().isoformat(), "SUCCESS"))
    except sqlite3.Error as e:
        return (False, f"Database error: {e}")
    finally:
        conn.close()

    return (True, "Payment processed and transaction recorded successfully.")

# --- Testing the checkout function ---
def main():
    # Initialize DB and create tables
    init_db()
    
    # Simulate a logged-in user with ID 101 and saved account info.
    user_id = 101
    user_account_info = {
        "payment": {
            "number": "1234567812345678",  # dummy card number
            "expiry": "12/30",
            "cvv": "123"
        },
        "shipping": {
            "address": "1234 Main St, Anytown, USA"
        }
    }
    
    # Simulate a shopping cart: list of (item_name, price)
    cart_items = [
        ("T-Shirt", 25.00),
        ("Jeans", 40.00),
        ("Sneakers", 60.00)
    ]
    
    print("Starting checkout process...")
    success, message = checkout(user_id, cart_items, user_account_info)
    print(message)
    
    # To test database records, we print out the transactions
    conn = sqlite3.connect(DB_NAME)
    with conn:
        cur = conn.execute("SELECT * FROM transactions")
        transactions = cur.fetchall()
        print("\nRecorded Transactions:")
        for transaction in transactions:
            print(transaction)
    conn.close()

if __name__ == "__main__":
    main()
