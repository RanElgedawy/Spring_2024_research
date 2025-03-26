import sqlite3
from cryptography.fernet import Fernet

# Create a database connection
conn = sqlite3.connect('payment_cards.db')
cursor = conn.cursor()

# Create the payment_cards table
cursor.execute("DROP TABLE IF EXISTS payment_cards")

cursor.execute('''
CREATE TABLE IF NOT EXISTS payment_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cardholder_name TEXT,
    encrypted_card_number TEXT,
    expiration_date TEXT,
    encrypted_cvv TEXT,
    default_status BOOLEAN
)
''')

# Generate a secure encryption key
key = Fernet.generate_key()
fernet = Fernet(key)

def register_card(cardholder_name, card_number, expiration_date, cvv):
    # Encrypt sensitive data
    encrypted_card_number = fernet.encrypt(card_number.encode())
    encrypted_cvv = fernet.encrypt(cvv.encode())

    # Insert card information into the database
    cursor.execute('''
    INSERT INTO payment_cards (cardholder_name, encrypted_card_number, expiration_date, encrypted_cvv, default_status)
    VALUES (?, ?, ?, ?, ?)
    ''', (cardholder_name, encrypted_card_number, expiration_date, encrypted_cvv, False))

    conn.commit()

# Example usage
register_card("John Doe", "1234567890123456", "01/25", "123")