import sqlite3
from cryptography.fernet import Fernet

# Database and encryption setup
DB_NAME = 'ecommerce.db'

# You should generate a key and keep it safe, this key is essential for decrypting your data
# This example is generating a key, but in production, you would load this from a secure location.
encryption_key = Fernet.generate_key()
cipher = Fernet(encryption_key)

def create_tables():
    """Create the database tables if they don't already exist"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number BLOB NOT NULL,
            card_holder_name TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cvv BLOB NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def encrypt_data(data: str) -> bytes:
    """Encrypt sensitive card information."""
    return cipher.encrypt(data.encode('utf-8'))

def decrypt_data(encrypted_data: bytes) -> str:
    """Decrypt sensitive card information."""
    return cipher.decrypt(encrypted_data).decode('utf-8')

def register_card(user_id: int, card_number: str, card_holder_name: str, expiry_date: str, cvv: str):
    """Register a new payment card for a user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    encrypted_card_number = encrypt_data(card_number)
    encrypted_cvv = encrypt_data(cvv)

    cursor.execute('''
        INSERT INTO payment_cards (user_id, card_number, card_holder_name, expiry_date, cvv)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, encrypted_card_number, card_holder_name, expiry_date, encrypted_cvv))

    conn.commit()
    conn.close()
    print("Card registered successfully!")

def retrieve_cards(user_id: int):
    """Retrieve and decrypt stored cards for a user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, card_number, card_holder_name, expiry_date, cvv FROM payment_cards
        WHERE user_id = ?
    ''', (user_id,))
    
    cards = cursor.fetchall()
    conn.close()

    decrypted_cards = []
    for card in cards:
        decrypted_card_number = decrypt_data(card[1])
        decrypted_cvv = decrypt_data(card[4])
        decrypted_cards.append({
            'Card ID': card[0],
            'Card Number': decrypted_card_number,
            'Card Holder Name': card[2],
            'Expiry Date': card[3],
            'CVV': decrypted_cvv
        })

    return decrypted_cards

# Testing the code
if __name__ == '__main__':
    # Create the tables
    create_tables()

    # Sample test user
    test_user_id = 1

    # Register a card (example data)
    register_card(
        user_id=test_user_id,
        card_number="4242424242424242",
        card_holder_name="John Doe",
        expiry_date="12/25",
        cvv="123"
    )

    # Retrieve the card data for testing
    cards = retrieve_cards(test_user_id)
    for card in cards:
        print(card)