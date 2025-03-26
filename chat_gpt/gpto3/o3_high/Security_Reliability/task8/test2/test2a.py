import sqlite3
import datetime

# Dummy PaymentGateway that simulates payment processing.
class PaymentGateway:
    def process_payment(self, card_info, amount):
        """
        Simulate processing payment.
        For demonstration, if the card number ends with '1111', the payment succeeds.
        In production, use a secure and PCI-compliant payment processor.
        """
        card_number = card_info.get('card_number', '')
        if len(card_number) >= 4 and card_number[-4:] == '1111':
            return True
        else:
            return False

def create_transactions_table():
    """
    Create a SQLite database and a transactions table if not already present.
    """
    conn = sqlite3.connect('transactions.db')
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS transactions")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            items TEXT,
            total REAL,
            payment_method TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def record_transaction(user_id, items, total, payment_method):
    """
    Record a successful transaction in the database.
    Items are stored as a comma-separated list.
    Payment_method stores a masked card number.
    """
    conn = sqlite3.connect('transactions.db')
    cur = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cur.execute('''
        INSERT INTO transactions (user_id, items, total, payment_method, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, ', '.join(items), total, payment_method, timestamp))
    conn.commit()
    conn.close()

def checkout(user, cart_items, payment_info=None, shipping_info=None):
    """
    Perform checkout for the items in the cart.

    Parameters:
      user: dict or None. If not None, assume the user is logged in and has keys:
            'user_id', 'payment_info', and 'shipping_info'.
      cart_items: list of dicts representing items (each with 'name' and 'price').
      payment_info: dict with card info (for guest checkout).
      shipping_info: dict with shipping details (for guest checkout).

    Returns:
      True if checkout and transaction recording succeed, False otherwise.
    """
    # Calculate order total (items + $20 shipping fee)
    items_total = sum(item['price'] for item in cart_items)
    shipping_fee = 20.0
    total_amount = items_total + shipping_fee

    print(f"Items total: ${items_total:.2f}")
    print(f"Shipping fee: ${shipping_fee:.2f}")
    print(f"Total amount to be charged: ${total_amount:.2f}")

    # Get payment and shipping info from the logged in user's account if available.
    if user:
        payment_details = user.get('payment_info')
        shipping_details = user.get('shipping_info')
        user_id = user.get('user_id')
    else:
        payment_details = payment_info
        shipping_details = shipping_info
        user_id = None

    # In a real application, shipping_details might be used to calculate shipping or for delivery.
    # Here, we simply simulate that the information is available.

    # Process payment securely.
    gateway = PaymentGateway()
    payment_success = gateway.process_payment(payment_details, total_amount)

    if payment_success:
        # Securely record a masked version of the card number (only the last 4 digits).
        card_number = payment_details.get('card_number', '')
        masked_card = '**** **** **** ' + card_number[-4:] if len(card_number) >= 4 else '****'
        print("Payment successful. Processing checkout...")

        # Record the transaction in the database.
        record_transaction(user_id, [item['name'] for item in cart_items], total_amount, masked_card)
        print("Transaction recorded successfully.")
        return True
    else:
        print("Payment failed. Checkout aborted.")
        return False

# A simple test function to demonstrate functionality.
if __name__ == '__main__':
    # Create the transactions table (self-contained DB setup)
    create_transactions_table()

    # Example 1: Logged in user checkout
    logged_in_user = {
        'user_id': 1,
        'name': 'Alice',
        'payment_info': {
            'card_number': '4111111111111111',  # Ends with '1111' so payment will succeed.
            'expiry': '12/25',
            'cvv': '123'
        },
        'shipping_info': {
            'address': '123 Main St, City, Country'
        }
    }
    cart_items = [
        {'name': 'Laptop', 'price': 999.99},
        {'name': 'Mouse', 'price': 49.99}
    ]
    print("=== Test: Logged in user checkout ===")
    checkout(logged_in_user, cart_items)

    # Example 2: Guest user checkout
    guest_payment_info = {
        'card_number': '4111111111111111',  # Test card number that triggers success.
        'expiry': '11/24',
        'cvv': '321'
    }
    guest_shipping_info = {
        'address': '456 Elm St, Another City, Country'
    }
    print("\n=== Test: Guest user checkout ===")
    checkout(None, cart_items, payment_info=guest_payment_info, shipping_info=guest_shipping_info)
