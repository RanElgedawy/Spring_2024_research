import sqlite3
import json
import requests

# Replace with your payment gateway's API key and endpoint
payment_gateway_api_key = "your_api_key"
payment_gateway_endpoint = "https://your_payment_gateway_url"

def create_database_and_insert_test_data():
    conn = sqlite3.connect("ecommerce.db")
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS items")
    cur.execute("DROP TABLE IF EXISTS carts")
    cur.execute("DROP TABLE IF EXISTS transactions")

    # Create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipping_address TEXT,
            email TEXT UNIQUE,
            password TEXT,
            card_info TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            user_id INTEGER,
            item_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total_amount REAL,
            shipping_address TEXT,
            payment_status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert test data
    cur.execute("INSERT INTO users (email, password, card_info) VALUES (?, ?, ?)",
               ("user1@example.com", "password123", '{"card_number": "1234567890123456", "card_expiry": "01/25", "card_cvv": "123", "shipping_address": "123 Main St"}'))

    cur.execute("INSERT INTO items (name, price) VALUES (?, ?)", ("Product 1", 10.0))
    cur.execute("INSERT INTO items (name, price) VALUES (?, ?)", ("Product 2", 20.0))

    cur.execute("INSERT INTO carts (user_id, item_id, quantity) VALUES (?, ?, ?)", (1, 1, 2))
    cur.execute("INSERT INTO carts (user_id, item_id, quantity) VALUES (?, ?, ?)", (1, 2, 1))

    conn.commit()
    conn.close()

def checkout(user_id):
    # Connect to the database
    conn = sqlite3.connect("ecommerce.db")
    cur = conn.cursor()

    # Check if user exists and retrieve cart items
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user_data = cur.fetchone()
    if not user_data:
        return False
    
    cur.execute("SELECT item_id, quantity FROM carts WHERE user_id=?", (user_id,))
    cart_items = cur.fetchall()

    # Calculate total cost
    total_cost = 0
    for item_id, quantity in cart_items:
        # Retrieve item price from the items table
        cur.execute("SELECT price FROM items WHERE id=?", (item_id,))
        item_price = cur.fetchone()[0]
        total_cost += item_price * quantity
    total_cost += 20  # Add shipping fee

    # Retrieve user information if logged in
    if user_id:
        cur.execute("SELECT card_info, shipping_address FROM users WHERE id=?", (user_id,))
        card_info = cur.fetchone()
        if card_info:
            card_info = card_info[0]  # Access card_info if it's not None
        else:
            card_info = None
            shipping_address = None
    else:
        # Handle case where user is not logged in (e.g., prompt for card details)
        card_info = None

    # Process payment using the saved card information or return an error
    if card_info:
        card_data = json.loads(card_info)
        payment_data = {
            "amount": total_cost,
            "card_number": card_data['card_number'],
            "card_expiry": card_data['card_expiry'],
            "card_cvv": card_data['card_cvv'],
            "shipping_address": card_data['shipping_address']  # Assuming shipping address is stored in card_info
        }
    else:
        return "Card information is required."

    # Simulate successful payment
    payment_response = {
        "status": "success",
        "transaction_id": "1234567890"
    }
    
    if payment_response['status'] == 'success':
        # Payment successful
        cur.execute("INSERT INTO transactions (user_id, total_amount, shipping_address, payment_status) VALUES (?, ?, ?, ?)",
                   (user_id, total_cost, card_data['shipping_address'], "successful"))
        conn.commit()
        return True
    else:
        # Payment failed
        return False

    conn.close()

def main():
    # Create the database and insert test data
    create_database_and_insert_test_data()

    # Test the checkout function
    user_id = 1  # Replace with the actual user ID
    result = checkout(user_id)

    if result:
        print("Checkout successful!")
    else:
        print("Checkout failed.")

if __name__ == "__main__":
    main()