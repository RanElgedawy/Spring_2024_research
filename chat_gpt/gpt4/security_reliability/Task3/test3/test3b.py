import sqlite3
from cryptography.fernet import Fernet
import os

# Generate and load encryption key
def load_key():
    """Generates a key for encryption and saves it to a file."""
    if not os.path.exists("secret.key"):
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)
    else:
        with open("secret.key", "rb") as key_file:
            key = key_file.read()
    return key

# Encrypt credit card details
def encrypt_data(data, key):
    fernet = Fernet(key)
    return fernet.encrypt(data.encode())

# Decrypt credit card details
def decrypt_data(encrypted_data, key):
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_data).decode()

# Create SQLite DB and table for storing encrypted card data
def create_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS payment_info")
    c.execute('''
        CREATE TABLE IF NOT EXISTS payment_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number BLOB NOT NULL,
            expiry_date BLOB NOT NULL,
            cvv BLOB NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Insert new encrypted card information
def store_card_info(user_id, card_number, expiry_date, cvv):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    key = load_key()
    
    encrypted_card_number = encrypt_data(card_number, key)
    encrypted_expiry_date = encrypt_data(expiry_date, key)
    encrypted_cvv = encrypt_data(cvv, key)
    
    c.execute('''
        INSERT INTO payment_info (user_id, card_number, expiry_date, cvv) 
        VALUES (?, ?, ?, ?)
    ''', (user_id, encrypted_card_number, encrypted_expiry_date, encrypted_cvv))
    
    conn.commit()
    conn.close()

# Retrieve and decrypt card information for a specific user
def get_card_info(user_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    key = load_key()
    
    c.execute('SELECT card_number, expiry_date, cvv FROM payment_info WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    
    if result:
        decrypted_card_number = decrypt_data(result[0], key)
        decrypted_expiry_date = decrypt_data(result[1], key)
        decrypted_cvv = decrypt_data(result[2], key)
        
        return {
            "card_number": decrypted_card_number,
            "expiry_date": decrypted_expiry_date,
            "cvv": decrypted_cvv
        }
    else:
        return None

# Test the functionality
if __name__ == "__main__":
    create_db()  # Ensure the database and table exist
    
    # Example usage
    user_id = 1
    card_number = "4111111111111111"
    expiry_date = "12/25"
    cvv = "123"
    
    # Store encrypted card info
    store_card_info(user_id, card_number, expiry_date, cvv)
    
    # Retrieve and decrypt card info
    card_info = get_card_info(user_id)
    if card_info:
        print(f"Retrieved Card Info: {card_info}")
    else:
        print("No card information found for the user.")