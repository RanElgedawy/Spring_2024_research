import sqlite3

def process_payment(card_info, amount):
    """
    Dummy payment processor. In a production scenario, integrate with a secure payment gateway.
    For testing, we simulate a successful payment only if the card number is the test card.
    """
    test_card_number = "4111111111111111"
    if card_info.get("number") == test_card_number:
        return True
    return False

def create_transactions_table(conn):
    """
    Creates the transactions table if it does not exist.
    Only minimal information is stored: user id, charged amount, timestamp, and status.
    """
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT
        )
    ''')
    conn.commit()

def checkout(conn, user, cart_items, card_info=None, shipping_info=None):
    """
    Processes the checkout:
      - Calculates the total (subtotal plus $20 shipping fee)
      - Uses the user's stored payment/shipping info if available or expects info for a guest.
      - Processes the payment and records the transaction in the database if successful.
    """
    # Calculate subtotal
    subtotal = sum(item["price"] * item.get("quantity", 1) for item in cart_items)
    shipping_fee = 20.0
    total = subtotal + shipping_fee

    # Retrieve payment information securely.
    if user and "payment_info" in user:
        payment_method = user["payment_info"]
    else:
        if card_info is None:
            raise Exception("No card information provided for guest checkout")
        payment_method = card_info

    # Retrieve shipping information.
    if user and "shipping_info" in user:
        shipping_details = user["shipping_info"]
    else:
        if shipping_info is None:
            raise Exception("No shipping information provided for guest checkout")
        shipping_details = shipping_info

    # Process the payment
    if not process_payment(payment_method, total):
        print("Payment failed. Checkout aborted.")
        return False

    # Record the transaction in the database using parameterized queries.
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (user_id, amount, status)
        VALUES (?, ?, ?)
    ''', (user["id"] if user else None, total, "SUCCESS"))
    conn.commit()
    print(f"Checkout successful! Total charged: ${total:.2f}")
    return True

def test_checkout():
    # Create an in-memory SQLite database.
    conn = sqlite3.connect(":memory:")
    create_transactions_table(conn)

    # Simulate a logged in user with stored payment and shipping information.
    user = {
        "id": 1,
        "payment_info": {"number": "4111111111111111", "expiry": "12/25", "cvv": "123"},
        "shipping_info": {"address": "123 Main St", "city": "Townsville", "zip": "12345"}
    }
    cart_items = [
        {"name": "T-shirt", "price": 25.0, "quantity": 2},
        {"name": "Jeans", "price": 40.0, "quantity": 1}
    ]
    print("Testing checkout for logged in user:")
    checkout(conn, user, cart_items)

    # Simulate a guest checkout.
    guest_user = None
    guest_card_info = {"number": "4111111111111111", "expiry": "12/25", "cvv": "123"}
    guest_shipping_info = {"address": "456 Other St", "city": "Village", "zip": "67890"}
    print("\nTesting checkout for guest user:")
    checkout(conn, guest_user, cart_items, card_info=guest_card_info, shipping_info=guest_shipping_info)

    # Display recorded transactions.
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    print("\nRecorded transactions:")
    for txn in transactions:
        print(txn)

    conn.close()

if __name__ == "__main__":
    test_checkout()
