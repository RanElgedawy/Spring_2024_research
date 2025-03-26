import os
import sqlite3
from cryptography.fernet import Fernet

# Use a file to persist the encryption key.
KEY_FILE = 'secret.key'

def load_or_create_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        print("Encryption key generated and saved.")
    else:
        with open(KEY_FILE, 'rb') as f:
            key = f.read()
        print("Encryption key loaded.")
    return key

# Initialize the encryption suite.
key = load_or_create_key()
cipher_suite = Fernet(key)

# Set up the SQLite database.
DB_FILE = 'cards.db'
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

def init_db():
    """Creates the cards table if it does not exist."""
    cursor.execute("DROP TABLE IF EXISTS cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            encrypted_card_number TEXT NOT NULL,
            expiration_date TEXT NOT NULL,
            cardholder_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    print("Database initialized.")

def add_card(user_id, card_number, expiration_date, cardholder_name):
    """
    Encrypts the card number and stores the payment card data.
    Note: CVV and other sensitive fields are not stored as per PCI guidelines.
    """
    encrypted_card_number = cipher_suite.encrypt(card_number.encode()).decode()
    cursor.execute('''
        INSERT INTO cards (user_id, encrypted_card_number, expiration_date, cardholder_name)
        VALUES (?, ?, ?, ?)
    ''', (user_id, encrypted_card_number, expiration_date, cardholder_name))
    conn.commit()
    print("Card added successfully for user:", user_id)

def get_cards(user_id):
    """Retrieves and decrypts all cards associated with the given user."""
    cursor.execute('''
        SELECT id, encrypted_card_number, expiration_date, cardholder_name, created_at 
        FROM cards WHERE user_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()
    cards = []
    for row in rows:
        decrypted_card_number = cipher_suite.decrypt(row[1].encode()).decode()
        card = {
            'id': row[0],
            'card_number': decrypted_card_number,
            'expiration_date': row[2],
            'cardholder_name': row[3],
            'created_at': row[4]
        }
        cards.append(card)
    return cards

def main():
    # Automatically set up the database.
    init_db()
    
    # For testing, we assume the user is logged in and has user_id = 1.
    user_id = 1

    # Test input: a dummy credit card (e.g., Visa test card number).
    test_card_number = "4111111111111111"  # Use only test numbers; never use real data in tests.
    test_expiration = "12/24"
    test_cardholder = "John Doe"

    # Add the test card.
    add_card(user_id, test_card_number, test_expiration, test_cardholder)

    # Retrieve and display the stored card details.
    cards = get_cards(user_id)
    print("\nRetrieved cards for user", user_id)
    for card in cards:
        print(card)

if __name__ == "__main__":
    main()
