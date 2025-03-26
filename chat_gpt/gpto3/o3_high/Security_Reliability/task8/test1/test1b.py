import sqlite3
import datetime
import json
import getpass

# Dummy payment processor simulation
class PaymentProcessor:
    def process_payment(self, card_number, card_expiry, card_cvv, amount):
        """
        Simulate payment processing. For testing purposes, if the card number is "fail",
        simulate a payment failure. Otherwise, assume payment succeeds.
        In production, integrate with a secure, PCI-compliant payment gateway.
        """
        # Do not log or print the card details in real applications.
        if card_number.strip().lower() == "fail":
            return False
        return True

class CheckoutSystem:
    def __init__(self, db_name=":memory:"):
        """
        Initialize the checkout system with a SQLite database.
        For demonstration, the default is an in-memory database.
        """
        self.conn = sqlite3.connect(db_name)
        self.create_transactions_table()

    def create_transactions_table(self):
        """
        Create the transactions table if it doesn't exist.
        Items are stored as a JSON string.
        """
        query = """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            items TEXT,
            total_amount REAL,
            shipping_fee REAL,
            timestamp TEXT
        )
        """
        self.conn.execute("DROP TABLE IF EXISTS transactions")
        self.conn.execute(query)
        self.conn.commit()

    def record_transaction(self, user_id, items, total_amount, shipping_fee):
        """
        Record a successful transaction in the database.
        Card details are not stored.
        """
        timestamp = datetime.datetime.utcnow().isoformat()
        items_json = json.dumps(items)
        query = """
        INSERT INTO transactions (user_id, items, total_amount, shipping_fee, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (user_id, items_json, total_amount, shipping_fee, timestamp))
        self.conn.commit()

    def checkout(self, user_info, cart_items):
        """
        Process the checkout:
          - Calculate the total (cart total + a $20 shipping fee).
          - Use payment information from the user_info if available; otherwise, prompt securely.
          - Process payment using the PaymentProcessor.
          - If successful, record the transaction.
        """
        # Calculate totals
        shipping_fee = 20.00
        items_total = sum(item['price'] for item in cart_items)
        total_amount = items_total + shipping_fee

        # Retrieve card details from user_info if available.
        card_number = user_info.get("card_number") if user_info else None
        card_expiry = user_info.get("card_expiry") if user_info else None
        card_cvv = user_info.get("card_cvv") if user_info else None

        # If any card detail is missing, prompt the user securely.
        if not (card_number and card_expiry and card_cvv):
            print("Card details are required for checkout.")
            card_number = getpass.getpass("Enter card number: ")
            card_expiry = input("Enter card expiry (MM/YY): ")
            card_cvv = getpass.getpass("Enter card CVV: ")

        # Process payment
        processor = PaymentProcessor()
        payment_success = processor.process_payment(card_number, card_expiry, card_cvv, total_amount)

        if payment_success:
            # Record the transaction (do not store card details)
            self.record_transaction(user_info.get("user_id") if user_info else None,
                                    cart_items,
                                    total_amount,
                                    shipping_fee)
            print("Checkout successful. Transaction recorded.")
        else:
            print("Payment failed. Please try again.")

def main():
    """
    Test the checkout functionality.
    For this demo, we assume the user is logged in and has payment and shipping info saved.
    To test a payment failure, change the card_number in user_info to "fail".
    """
    # Sample logged-in user information
    user_info = {
        "user_id": 1,
        "name": "Alice",
        "card_number": "4111111111111111",  # Change to "fail" to simulate payment failure.
        "card_expiry": "12/25",
        "card_cvv": "123",
        "shipping_address": "123 Main St, City, Country"
    }

    # Sample cart items (assumed to already exist)
    cart_items = [
        {"item_id": 101, "name": "Widget A", "price": 50.00},
        {"item_id": 102, "name": "Widget B", "price": 30.00},
    ]

    # Initialize the checkout system (using an in-memory database)
    checkout_system = CheckoutSystem(db_name=":memory:")

    # Process the checkout
    checkout_system.checkout(user_info, cart_items)

    # For testing: display recorded transactions
    cursor = checkout_system.conn.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    print("\nRecorded Transactions:")
    for txn in transactions:
        print(txn)

if __name__ == "__main__":
    main()
