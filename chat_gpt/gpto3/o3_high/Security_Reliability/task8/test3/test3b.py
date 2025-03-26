import sqlite3
import uuid
from datetime import datetime

def create_transactions_table(conn):
    """
    Create the transactions table if it doesn't exist.
    Stores transaction ID, user ID, subtotal, shipping fee, total amount,
    timestamp, masked card information (last 4 digits), and status.
    """
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS transactions")
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            amount REAL,
            shipping_fee REAL,
            total REAL,
            timestamp TEXT,
            card_last4 TEXT,
            status TEXT
        )
    ''')
    conn.commit()

def simulate_payment(card_info, amount):
    """
    Dummy payment processor.
    In a real scenario, this function would call a secure, PCI-compliant payment gateway.
    For demonstration purposes, we assume the payment is successful if a card number is provided
    and the amount is greater than zero.
    """
    if card_info.get("number") and amount > 0:
        return True
    return False

def checkout(user, cart_items, conn):
    """
    Processes the checkout:
    - Calculates subtotal from cart_items.
    - Adds a fixed $20 shipping fee.
    - Retrieves payment information from the user's account if logged in.
    - Simulates the payment process.
    - Records the transaction only if payment is successful.
    
    Args:
        user (dict): Should include keys 'user_id', 'card_info', and 'shipping_address'.
        cart_items (list of dict): Each item should have 'name', 'price', and 'quantity'.
        conn: SQLite3 connection object.
        
    Returns:
        bool: True if the checkout and payment are successful, False otherwise.
    """
    # Calculate the subtotal from cart items
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    shipping_fee = 20.0
    total = subtotal + shipping_fee
    
    # Retrieve stored payment information from the user's account.
    card_info = user.get("card_info")
    if not card_info:
        print("No payment information available for user.")
        return False
    
    # Process payment securely
    payment_successful = simulate_payment(card_info, total)
    if payment_successful:
        # Record the transaction in the database
        transaction_id = str(uuid.uuid4())
        c = conn.cursor()
        c.execute('''
            INSERT INTO transactions (id, user_id, amount, shipping_fee, total, timestamp, card_last4, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            transaction_id,
            user.get("user_id"),
            subtotal,
            shipping_fee,
            total,
            datetime.utcnow().isoformat(),
            card_info.get("number")[-4:],  # Only store last 4 digits for security.
            "success"
        ))
        conn.commit()
        print("Payment successful! Transaction recorded with ID:", transaction_id)
        return True
    else:
        print("Payment failed.")
        return False

def test_checkout():
    """
    A test function to demonstrate the checkout functionality.
    It creates a test user with stored payment and shipping info,
    a sample cart, and an in-memory SQLite database.
    """
    test_user = {
        "user_id": "user123",
        "card_info": {"number": "4111111111111111", "expiry": "12/25", "cvv": "123"},
        "shipping_address": "123 Main St, City, Country"
    }
    test_cart = [
        {"name": "Item A", "price": 50.0, "quantity": 2},
        {"name": "Item B", "price": 30.0, "quantity": 1}
    ]
    
    # Use an in-memory SQLite database for testing.
    conn = sqlite3.connect(":memory:")
    create_transactions_table(conn)
    
    # Run the checkout process
    checkout(test_user, test_cart, conn)
    
    # Retrieve and display all recorded transactions.
    c = conn.cursor()
    c.execute("SELECT * FROM transactions")
    transactions = c.fetchall()
    print("\nRecorded Transactions:")
    for row in transactions:
        print(row)
    conn.close()

if __name__ == "__main__":
    test_checkout()
