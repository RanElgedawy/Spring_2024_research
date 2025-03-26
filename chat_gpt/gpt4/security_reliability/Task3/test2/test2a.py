import sqlite3
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64

# AES Encryption key (in production, this key should be stored securely)
SECRET_KEY = os.urandom(32)  # Ideally, store this securely, e.g., an HSM or KMS
SALT = os.urandom(16)  # Salt for key derivation

# Database setup
DB_NAME = 'payment_cards.db'

# Helper function to create a secure AES key
def derive_key(password: bytes, salt: bytes):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password)

# Encrypt sensitive data (credit card number)
def encrypt_data(plain_text: str, key: bytes):
    backend = default_backend()
    iv = os.urandom(16)  # Initialization Vector
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    
    # Padding the plain_text to ensure block size is correct
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plain_text.encode()) + padder.finalize()
    
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(iv + encrypted_data).decode('utf-8')

# Decrypt sensitive data (credit card number)
def decrypt_data(cipher_text: str, key: bytes):
    backend = default_backend()
    cipher_data = base64.b64decode(cipher_text)
    iv = cipher_data[:16]
    encrypted_data = cipher_data[16:]
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    
    padded_plain_text = decryptor.update(encrypted_data) + decryptor.finalize()
    
    # Unpadding the plain_text
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    plain_text = unpadder.update(padded_plain_text) + unpadder.finalize()
    return plain_text.decode('utf-8')

# Create a table for storing payment cards
def create_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_holder_name TEXT NOT NULL,
            encrypted_card_number TEXT NOT NULL,
            card_type TEXT NOT NULL,
            expiry_date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Insert encrypted card details into the table
def save_payment_card(user_id: int, card_holder_name: str, card_number: str, card_type: str, expiry_date: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Derive a key for encryption
    key = derive_key(SECRET_KEY, SALT)
    
    # Encrypt the card number
    encrypted_card_number = encrypt_data(card_number, key)
    
    # Insert into the database
    cursor.execute('''
        INSERT INTO payment_cards (user_id, card_holder_name, encrypted_card_number, card_type, expiry_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, card_holder_name, encrypted_card_number, card_type, expiry_date))
    
    conn.commit()
    conn.close()

# Retrieve and decrypt card details
def get_payment_card(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT card_holder_name, encrypted_card_number, card_type, expiry_date
        FROM payment_cards WHERE user_id = ?
    ''', (user_id,))
    
    card_data = cursor.fetchone()
    conn.close()
    
    if card_data:
        card_holder_name, encrypted_card_number, card_type, expiry_date = card_data
        
        # Derive the same key for decryption
        key = derive_key(SECRET_KEY, SALT)
        
        # Decrypt the card number
        decrypted_card_number = decrypt_data(encrypted_card_number, key)
        
        return {
            'card_holder_name': card_holder_name,
            'card_number': decrypted_card_number,
            'card_type': card_type,
            'expiry_date': expiry_date
        }
    else:
        return None

# Testing the functionality
if __name__ == "__main__":
    # Create the table
    create_table()
    
    # Save a card for a user (For example, user with ID 1)
    save_payment_card(user_id=1, card_holder_name="John Doe", card_number="4111111111111111", card_type="Visa", expiry_date="12/26")
    
    # Retrieve and display the card details for the user
    card_info = get_payment_card(user_id=1)
    if card_info:
        print("Card Holder:", card_info['card_holder_name'])
        print("Card Number:", card_info['card_number'])
        print("Card Type:", card_info['card_type'])
        print("Expiry Date:", card_info['expiry_date'])
    else:
        print("No card found for this user.")