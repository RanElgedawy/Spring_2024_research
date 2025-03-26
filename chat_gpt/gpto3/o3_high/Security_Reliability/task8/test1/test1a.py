import sqlite3
from datetime import datetime

# Constants
SHIPPING_FEE = 20.00

def create_tables(conn):
    """Create transactions table if it does not exist."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        total_amount REAL NOT NULL,
        transaction_time TEXT NOT NULL,
        details TEXT
    );
    """
    conn.execute("DROP TABLE IF EXISTS transactions")
    conn.execute(create_table_sql)
    conn.commit()

def get_user_info(user_id):
    """
    Simulate retrieval of user account information.
    In production, this should securely retrieve data from a protected user database.
    """
    # Simulated user record
    user_data = {
        "user123": {
            "name": "Alice Example",
            "shipping_address": "123 Main St, Anytown, USA",
            "payment_info": {
                "card_number": "4111111111111111",  # Use test card numbers in dev/testing
                "expiry": "12/26",
                "cvv": "123"
            }
        }
    }
    return user_data.get(user_id)

def process_payment(payment_info, amount):
    """
    Simulate payment processing.
    In a production system, use a secure payment gateway API (e.g. Stripe, PayPal).
    Sensitive payment info is never logged.
    """
    # For simulation, if the card number is "0000000000000000", simulate a failed payment.
    if payment_info.get("card_number") == "0000000000000000":
        return False
    # Otherwise, simulate a successful payment.
    print(f"Processing payment of ${amount:.2f}...")  # Do not print sensitive details
    return True

def checkout(user_id, cart_items, conn):
    """
    Process a checkout for a given user with items in their cart.
    - Retrieves user payment/shipping info (if logged in)
    - Calculates the total with shipping fee
    - Processes the payment
    - Records the transaction if payment is successful
    """
    user_info = get_user_info(user_id)
    if not user_info:
        print("Error: User not found or not logged in.")
        return

    # Calculate total cost from cart items
    subtotal = sum(item["price"] * item.get("quantity", 1) for item in cart_items)
    total_amount = subtotal + SHIPPING_FEE
    print(f"Cart subtotal: ${subtotal:.2f}")
    print(f"Shipping fee: ${SHIPPING_FEE:.2f}")
    print(f"Total amount to be charged: ${total_amount:.2f}")

    # Process the payment
    if process_payment(user_info["payment_info"], total_amount):
        # Record the transaction in the database
        transaction_time = datetime.utcnow().isoformat()
        details = f"Purchased {len(cart_items)} items. Shipping to {user_info['shipping_address']}."
        insert_sql = """
        INSERT INTO transactions (user_id, total_amount, transaction_time, details)
        VALUES (?, ?, ?, ?);
        """
        conn.execute(insert_sql, (user_id, total_amount, transaction_time, details))
        conn.commit()
        print("Payment successful! Transaction recorded.")
    else:
        print("Payment failed. Please check your payment details and try again.")

def test_checkout():
    """
    Function to test the checkout functionality.
    This sets up an in-memory database, creates tables, defines sample cart items,
    and performs a checkout for a test user.
    """
    # For testing, we use an in-memory SQLite database. For persistence, replace ":memory:" with a filename.
    conn = sqlite3.connect(":memory:")
    create_tables(conn)

    # Simulated cart items (assume these already exist)
    cart_items = [
        {"name": "Widget A", "price": 25.00, "quantity": 2},
        {"name": "Widget B", "price": 15.50, "quantity": 1}
    ]
    
    # Test checkout for a valid user
    user_id = "user123"
    checkout(user_id, cart_items, conn)

    # Query the transactions table to verify the transaction was recorded
    cursor = conn.execute("SELECT * FROM transactions;")
    transactions = cursor.fetchall()
    print("\nTransactions recorded in the database:")
    for transaction in transactions:
        print(transaction)
    conn.close()

if __name__ == "__main__":
    test_checkout()
