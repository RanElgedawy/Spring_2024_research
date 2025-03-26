import sqlite3
import datetime
import json

# Initialize the database and create the transactions table if it doesn't exist.
def initialize_db():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            items TEXT,
            total_amount REAL,
            shipping_fee REAL,
            transaction_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

# A simple payment processor class that simulates payment processing.
class PaymentProcessor:
    def process_payment(self, card_info, amount):
        """
        Process a payment for the given amount.
        For demonstration, the payment is successful only if the card number is '4111111111111111'.
        In a production system, you would integrate with a secure payment gateway.
        """
        print("Processing payment of ${:.2f}".format(amount))
        # Do not log full card details in production; here we only use a test card number.
        if card_info.get('card_number') == '4111111111111111':
            return True
        else:
            return False

# Record the successful transaction in the database securely.
def record_transaction(user_id, cart_items, total_amount, shipping_fee):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    transaction_time = datetime.datetime.now().isoformat()
    items_json = json.dumps(cart_items)  # Convert list of cart items to JSON.
    # Use parameterized queries to protect against SQL injection.
    cursor.execute('''
        INSERT INTO transactions (user_id, items, total_amount, shipping_fee, transaction_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, items_json, total_amount, shipping_fee, transaction_time))
    conn.commit()
    conn.close()
    print("Transaction recorded successfully.")

# The main checkout function.
def checkout(user_id, cart_items, payment_info=None, shipping_info=None):
    """
    Processes the checkout for a given user.
    
    If payment_info or shipping_info is None, we simulate fetching those details from the user's account.
    Calculates the total (including a fixed $20 shipping fee), processes the payment, and records the transaction if successful.
    """
    # Simulate fetching payment info from the user's account if not provided.
    if payment_info is None:
        payment_info = {
            'card_number': '4111111111111111',  # Test card that triggers a successful payment.
            'expiration_date': '12/25',
            'cvv': '123'
        }
    # Simulate fetching shipping info from the user's account if not provided.
    if shipping_info is None:
        shipping_info = {
            'address': '123 Main St',
            'city': 'Anytown',
            'zip': '12345',
            'country': 'USA'
        }
    
    # Calculate the subtotal from cart items.
    subtotal = sum(item['price'] * item.get('quantity', 1) for item in cart_items)
    shipping_fee = 20.0
    total = subtotal + shipping_fee
    
    print("Subtotal: ${:.2f}".format(subtotal))
    print("Shipping Fee: ${:.2f}".format(shipping_fee))
    print("Total: ${:.2f}".format(total))
    
    # Process the payment.
    processor = PaymentProcessor()
    payment_success = processor.process_payment(payment_info, total)
    
    if payment_success:
        print("Payment processed successfully.")
        # Record the transaction in the database.
        record_transaction(user_id, cart_items, total, shipping_fee)
    else:
        print("Payment failed. Transaction cancelled.")

# Test functionality.
def main():
    # Initialize the database (creates the transactions table if needed).
    initialize_db()
    
    # Example cart items (assumed to have been added previously).
    cart_items = [
        {'name': 'Widget A', 'price': 30.0, 'quantity': 2},
        {'name': 'Widget B', 'price': 45.0, 'quantity': 1}
    ]
    # Simulate a logged-in user with user_id 1.
    user_id = 1
    
    print("=== Checkout with Valid Payment Info ===")
    checkout(user_id, cart_items)
    
    # Test the checkout with invalid card information to simulate a failed payment.
    print("\n=== Checkout with Invalid Payment Info ===")
    invalid_payment_info = {
        'card_number': '1234567890123456',  # An invalid card number for simulation.
        'expiration_date': '12/25',
        'cvv': '123'
    }
    checkout(user_id, cart_items, payment_info=invalid_payment_info)

if __name__ == '__main__':
    main()
