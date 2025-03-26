import sqlite3
from datetime import datetime

def init_db(conn):
    """Initializes the database by creating the transactions table."""
    conn.execute("DROP TABLE IF EXISTS transactions")
    conn.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        total_amount REAL,
        shipping_address TEXT,
        transaction_date TEXT,
        card_last4 TEXT
    )
    ''')
    conn.commit()

def process_payment(payment_info, amount):
    """
    Simulates processing a payment.
    In a production system, replace this with secure integration with a payment gateway.
    Here, we simulate success if the card number is exactly 16 digits.
    """
    card_number = payment_info.get("card_number", "")
    if len(card_number) == 16:
        return True
    return False

def record_transaction(conn, user_id, total_amount, shipping_address, card_last4):
    """Records the successful transaction in the database."""
    transaction_date = datetime.utcnow().isoformat()
    conn.execute('''
    INSERT INTO transactions (user_id, total_amount, shipping_address, transaction_date, card_last4)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, total_amount, shipping_address, transaction_date, card_last4))
    conn.commit()

def checkout(user, cart_items, conn):
    """
    Processes checkout:
    - Calculates subtotal and adds a $20 shipping fee.
    - Retrieves user's shipping and payment info.
    - Proceeds only if payment is successful.
    - Records the transaction securely.
    """
    subtotal = sum(item.get("price", 0) for item in cart_items)
    shipping_fee = 20
    total = subtotal + shipping_fee

    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Shipping Fee: ${shipping_fee:.2f}")
    print(f"Total: ${total:.2f}")

    shipping_address = user.get("shipping_address")
    payment_info = user.get("payment_info")

    if not shipping_address or not payment_info:
        print("User information incomplete. Cannot proceed with checkout.")
        return False

    if process_payment(payment_info, total):
        print("Payment successful. Recording transaction.")
        # Only store the last 4 digits of the card for security reasons.
        card_last4 = payment_info["card_number"][-4:]
        record_transaction(conn, user.get("id"), total, shipping_address, card_last4)
        return True
    else:
        print("Payment failed. Transaction aborted.")
        return False

def main():
    # Create an in-memory SQLite database for testing.
    conn = sqlite3.connect(":memory:")
    init_db(conn)

    # Simulated logged-in user with shipping and payment information.
    user = {
        "id": 1,
        "shipping_address": "123 Main St, Anytown, USA",
        "payment_info": {
            "card_number": "1234567812345678",  # Dummy card number (16 digits)
            "expiry": "12/25",
            "cvv": "123"
        }
    }

    # Simulated cart with items.
    cart_items = [
        {"name": "T-shirt", "price": 25.00},
        {"name": "Jeans", "price": 50.00},
        {"name": "Hat", "price": 15.00}
    ]

    if checkout(user, cart_items, conn):
        print("Checkout completed successfully.")
    else:
        print("Checkout failed.")

    # For testing: Query the transactions table and print the results.
    cursor = conn.execute("SELECT * FROM transactions")
    for row in cursor.fetchall():
        print(row)

if __name__ == "__main__":
    main()
