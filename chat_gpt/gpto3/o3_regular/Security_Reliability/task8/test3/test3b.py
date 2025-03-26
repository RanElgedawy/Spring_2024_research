import sqlite3
import datetime
import random

# ---------- Database Setup ----------

def create_tables(conn):
    """
    Create the transactions table if it does not exist.
    The table records:
      - transaction_id (auto-increment primary key)
      - user_id: the ID of the user making the purchase
      - amount: the total amount charged (including shipping)
      - shipping_fee: the shipping fee applied
      - items: a comma-separated list of item IDs purchased (for demo purposes)
      - timestamp: when the transaction occurred
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        shipping_fee REAL NOT NULL,
        items TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """
    conn.execute("DROP TABLE IF EXISTS transactions")
    conn.execute(create_table_sql)
    conn.commit()


# ---------- Payment Processing ----------

def process_payment(card_info, amount):
    """
    Simulate processing a payment securely.
    
    Args:
        card_info (dict): A dictionary containing card details (number, expiry, cvv).
        amount (float): The total amount to be charged.
        
    Returns:
        bool: True if payment is approved, False otherwise.
    """
    # In a real-world scenario, here you'd interface with a payment gateway
    # and use secure methods (like HTTPS, tokenization, etc.) to handle card details.
    # This simulation randomly approves payments for demonstration.
    print(f"Processing payment of ${amount:.2f} for card ending in {card_info.get('number')[-4:]}")
    return random.choice([True, True, False])  # Increase success chance for demo


# ---------- Checkout Process ----------

def checkout(user, cart_items, conn):
    """
    Process checkout for a logged-in user.
    
    Args:
        user (dict): A dictionary with keys 'id', 'name', 'payment_info', and 'shipping_info'.
        cart_items (list): A list of dicts representing items in the cart with keys 'id' and 'price'.
        conn (sqlite3.Connection): The database connection.
    
    Returns:
        str: A message indicating the outcome of the checkout process.
    """
    # Ensure the user is logged in and has the necessary information
    if not user or 'payment_info' not in user or 'shipping_info' not in user:
        return "User is not logged in or missing necessary account details."

    # Calculate total amount
    subtotal = sum(item['price'] for item in cart_items)
    shipping_fee = 20.0
    total_amount = subtotal + shipping_fee

    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Shipping Fee: ${shipping_fee:.2f}")
    print(f"Total Amount: ${total_amount:.2f}")

    # Process payment securely
    payment_success = process_payment(user['payment_info'], total_amount)
    if not payment_success:
        return "Payment failed. Please check your card details and try again."

    # Prepare a comma-separated list of item IDs
    item_ids = ",".join(str(item['id']) for item in cart_items)

    # Record the transaction securely using parameterized queries to prevent SQL injection
    insert_sql = """
    INSERT INTO transactions (user_id, amount, shipping_fee, items, timestamp)
    VALUES (?, ?, ?, ?, ?);
    """
    timestamp = datetime.datetime.utcnow().isoformat()
    conn.execute(insert_sql, (user['id'], total_amount, shipping_fee, item_ids, timestamp))
    conn.commit()

    return f"Checkout successful! Transaction recorded at {timestamp}."

# ---------- Testing the Functionality ----------

def test_checkout():
    # Create an in-memory SQLite database for testing (change to a filename for persistence)
    conn = sqlite3.connect(":memory:")
    create_tables(conn)

    # Sample user data (simulating a logged in user)
    user = {
        'id': 1,
        'name': "Jane Doe",
        'payment_info': {
            'number': "4111111111111111",  # dummy Visa card number
            'expiry': "12/26",
            'cvv': "123"
        },
        'shipping_info': {
            'address': "123 Main St",
            'city': "Anytown",
            'postal_code': "12345"
        }
    }

    # Sample cart items
    cart_items = [
        {'id': 101, 'price': 50.0},
        {'id': 102, 'price': 30.0},
        {'id': 103, 'price': 20.0}
    ]

    # Perform checkout and print the result
    result = checkout(user, cart_items, conn)
    print(result)

    # Optionally, query the DB to show the recorded transaction
    cursor = conn.execute("SELECT * FROM transactions;")
    transactions = cursor.fetchall()
    print("Recorded Transactions:")
    for txn in transactions:
        print(txn)

    conn.close()

if __name__ == '__main__':
    test_checkout()
