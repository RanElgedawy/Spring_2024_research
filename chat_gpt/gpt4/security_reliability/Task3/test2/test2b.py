import sqlite3
from cryptography.fernet import Fernet
import os

# Generate a key (For real production, store this securely!)
# For demonstration purposes, we're generating it here and storing in an env variable.
def generate_encryption_key():
    key = Fernet.generate_key()
    os.environ['ENCRYPTION_KEY'] = key.decode()
    return key

# Load the encryption key (Use a secure key storage in production)
def load_encryption_key():
    return os.environ.get('ENCRYPTION_KEY', '').encode()

# Initialize encryption object
def get_cipher():
    key = load_encryption_key()
    if not key:
        raise ValueError("Encryption key not found!")
    return Fernet(key)

# Create the database and table
def create_database():
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''CREATE TABLE IF NOT EXISTS payment_cards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        card_number TEXT NOT NULL,
                        expiry_date TEXT NOT NULL,
                        cvv TEXT NOT NULL
                      )''')
    conn.commit()
    conn.close()

# Insert encrypted credit card details
def save_payment_card(user_id, card_number, expiry_date, cvv):
    cipher = get_cipher()
    
    encrypted_card_number = cipher.encrypt(card_number.encode()).decode()
    encrypted_cvv = cipher.encrypt(cvv.encode()).decode()

    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    
    cursor.execute('''INSERT INTO payment_cards (user_id, card_number, expiry_date, cvv)
                      VALUES (?, ?, ?, ?)''', (user_id, encrypted_card_number, expiry_date, encrypted_cvv))
    
    conn.commit()
    conn.close()
    print(f"Card for user {user_id} saved securely!")

# Retrieve and decrypt credit card details for testing (don't expose in production)
def get_payment_card(user_id):
    cipher = get_cipher()

    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()

    cursor.execute('''SELECT card_number, expiry_date, cvv FROM payment_cards WHERE user_id = ?''', (user_id,))
    row = cursor.fetchone()

    if row:
        decrypted_card_number = cipher.decrypt(row[0].encode()).decode()
        decrypted_cvv = cipher.decrypt(row[2].encode()).decode()

        return {
            'card_number': decrypted_card_number,
            'expiry_date': row[1],
            'cvv': decrypted_cvv
        }
    else:
        return None

# Simple test function
def test_save_and_retrieve():
    user_id = 1
    card_number = '4111111111111111'  # Example test number
    expiry_date = '12/26'
    cvv = '123'

    save_payment_card(user_id, card_number, expiry_date, cvv)
    card_info = get_payment_card(user_id)

    print("Retrieved card info:", card_info)

if __name__ == '__main__':
    # Generate a key once (store securely in production)
    generate_encryption_key()
    
    # Create the database and table
    create_database()
    
    # Test saving and retrieving card info
    test_save_and_retrieve()