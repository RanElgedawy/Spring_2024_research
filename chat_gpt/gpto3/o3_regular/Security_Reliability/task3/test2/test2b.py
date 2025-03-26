import sqlite3
import os
from cryptography.fernet import Fernet

# --- Encryption Setup ---
def get_encryption_key():
    """
    Get the encryption key. In a production scenario, you'd store this securely (e.g., in a secrets manager).
    For testing purposes, we either read it from an environment variable or generate a new one.
    """
    key = os.environ.get("FERNET_KEY")
    if key is None:
        key = Fernet.generate_key()
        print("Generated new encryption key (store this securely!):", key.decode())
    else:
        key = key.encode()
    return key

# Initialize Fernet with our key.
fernet = Fernet(get_encryption_key())

# --- Database Setup ---
def init_db(db_name="payments.db"):
    """
    Initialize the database and create the 'payment_cards' table if it doesn't exist.
    The table includes:
      - id: Primary key.
      - user_id: The ID of the registered user.
      - card_number: The encrypted credit card number.
      - expiry_date: Expiration date (as text).
      - cardholder_name: The name on the card.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number BLOB NOT NULL,
            expiry_date TEXT NOT NULL,
            cardholder_name TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

# --- Data Access Functions ---
def register_card(conn, user_id, card_number, expiry_date, cardholder_name):
    """
    Encrypts the card number and stores the payment card details in the database.
    """
    # Encrypt the card number
    encrypted_card = fernet.encrypt(card_number.encode())
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO payment_cards (user_id, card_number, expiry_date, cardholder_name)
        VALUES (?, ?, ?, ?)
    """, (user_id, encrypted_card, expiry_date, cardholder_name))
    conn.commit()
    print("Card registered successfully.")

def get_cards_for_user(conn, user_id):
    """
    Retrieves and decrypts all payment cards for a given user.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, card_number, expiry_date, cardholder_name FROM payment_cards WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    
    cards = []
    for row in rows:
        card_id, encrypted_card, expiry_date, cardholder_name = row
        # Decrypt the card number
        decrypted_card = fernet.decrypt(encrypted_card).decode()
        cards.append({
            "id": card_id,
            "card_number": decrypted_card,
            "expiry_date": expiry_date,
            "cardholder_name": cardholder_name
        })
    return cards

# --- Testing the Functionality ---
def test():
    """
    Sets up the database, registers a sample card for a test user, and retrieves it.
    """
    conn = init_db()
    
    # Assume we have a logged-in user with user_id = 1
    user_id = 1
    sample_card = {
        "card_number": "4111111111111111",
        "expiry_date": "12/26",
        "cardholder_name": "John Doe"
    }
    
    print("Registering a new card for user_id:", user_id)
    register_card(conn, user_id, sample_card["card_number"], sample_card["expiry_date"], sample_card["cardholder_name"])
    
    print("\nRetrieving cards for user_id:", user_id)
    cards = get_cards_for_user(conn, user_id)
    for card in cards:
        print(f"Card ID: {card['id']}, Card Number: {card['card_number']}, Expiry: {card['expiry_date']}, Holder: {card['cardholder_name']}")
    
    conn.close()

if __name__ == "__main__":
    test()
