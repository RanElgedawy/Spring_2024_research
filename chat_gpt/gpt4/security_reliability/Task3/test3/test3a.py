import sqlite3
from cryptography.fernet import Fernet
import os

# Generate or load encryption key
def load_or_create_key():
    if os.path.exists("encryption_key.key"):
        with open("encryption_key.key", "rb") as key_file:
            key = key_file.read()
    else:
        key = Fernet.generate_key()
        with open("encryption_key.key", "wb") as key_file:
            key_file.write(key)
    return key

# Encryption and decryption utilities
class EncryptionManager:
    def __init__(self, key):
        self.fernet = Fernet(key)
    
    def encrypt(self, data):
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data):
        return self.fernet.decrypt(encrypted_data.encode()).decode()

# Initialize the database and create the necessary table
def initialize_database():
    conn = sqlite3.connect('payment_cards.db')
    cursor = conn.cursor()
    
    # Create table for storing card information
    cursor.execute("DROP TABLE IF EXISTS cards")
    cursor.execute('''CREATE TABLE IF NOT EXISTS cards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        card_number TEXT NOT NULL,
                        expiry_date TEXT NOT NULL,
                        cardholder_name TEXT NOT NULL,
                        cvv TEXT NOT NULL
                    )''')
    conn.commit()
    conn.close()

# Function to register a new card
def register_card(user_id, card_number, expiry_date, cardholder_name, cvv, encryption_manager):
    conn = sqlite3.connect('payment_cards.db')
    cursor = conn.cursor()
    
    # Encrypt sensitive information
    encrypted_card_number = encryption_manager.encrypt(card_number)
    encrypted_cvv = encryption_manager.encrypt(cvv)
    
    # Insert the card into the database
    cursor.execute('''INSERT INTO cards (user_id, card_number, expiry_date, cardholder_name, cvv)
                      VALUES (?, ?, ?, ?, ?)''', 
                      (user_id, encrypted_card_number, expiry_date, cardholder_name, encrypted_cvv))
    conn.commit()
    conn.close()

# Function to retrieve and decrypt card information
def get_card(user_id, encryption_manager):
    conn = sqlite3.connect('payment_cards.db')
    cursor = conn.cursor()
    
    # Retrieve the card details from the database
    cursor.execute("SELECT card_number, expiry_date, cardholder_name, cvv FROM cards WHERE user_id=?", (user_id,))
    card = cursor.fetchone()
    
    if card:
        decrypted_card_number = encryption_manager.decrypt(card[0])
        decrypted_cvv = encryption_manager.decrypt(card[3])
        print(f"Card Number: {decrypted_card_number}, Expiry Date: {card[1]}, Cardholder Name: {card[2]}, CVV: {decrypted_cvv}")
    else:
        print("No card found for this user.")
    
    conn.close()

# Main logic for testing
if __name__ == "__main__":
    key = load_or_create_key()
    encryption_manager = EncryptionManager(key)
    
    # Initialize database and table
    initialize_database()

    # Test data
    test_user_id = 1
    test_card_number = "4111111111111111"
    test_expiry_date = "12/26"
    test_cardholder_name = "John Doe"
    test_cvv = "123"
    
    # Register the card
    register_card(test_user_id, test_card_number, test_expiry_date, test_cardholder_name, test_cvv, encryption_manager)
    
    # Retrieve and display the card (this will print the decrypted details)
    get_card(test_user_id, encryption_manager)