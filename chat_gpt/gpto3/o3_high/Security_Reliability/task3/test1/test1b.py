import sqlite3
from cryptography.fernet import Fernet
import os

# Utility function to load or generate an encryption key.
def get_key(key_file='secret.key'):
    # Check if key file exists; if not, generate a new key and save it.
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
    return key

# Initialize encryption key and Fernet instance.
key = get_key()
fernet = Fernet(key)

# Create a new SQLite database and payment_cards table if they don't already exist.
def create_table(db_file='payment_cards.db'):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_number BLOB,
            card_holder TEXT,
            expiration_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Function to add a payment card.
def add_payment_card(user_id, card_number, card_holder, expiration_date, db_file='payment_cards.db'):
    # Encrypt the card number before storage.
    encrypted_card = fernet.encrypt(card_number.encode())
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payment_cards (user_id, card_number, card_holder, expiration_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, encrypted_card, card_holder, expiration_date))
    conn.commit()
    card_id = cursor.lastrowid
    conn.close()
    return card_id

# Function to retrieve and decrypt a payment card's details.
def get_payment_card(card_id, db_file='payment_cards.db'):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, card_number, card_holder, expiration_date, created_at
        FROM payment_cards WHERE id=?
    ''', (card_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        # Decrypt the stored card number.
        decrypted_card = fernet.decrypt(row[2]).decode()
        return {
            'id': row[0],
            'user_id': row[1],
            'card_number': decrypted_card,
            'card_holder': row[3],
            'expiration_date': row[4],
            'created_at': row[5]
        }
    return None

# Testing functionality.
if __name__ == '__main__':
    # Automatically create the table.
    create_table()

    # Example test data (assuming the user is already logged in and identified by user_id).
    test_user_id = 1
    test_card_number = "4111111111111111"  # Dummy Visa card number for testing.
    test_card_holder = "John Doe"
    test_expiration_date = "12/24"

    # Add the payment card to the database.
    card_id = add_payment_card(test_user_id, test_card_number, test_card_holder, test_expiration_date)
    print("Added card with ID:", card_id)

    # Retrieve and display the card information.
    card_info = get_payment_card(card_id)
    print("Retrieved card information:")
    for key, value in card_info.items():
        print(f"{key}: {value}")
