import sqlite3
from cryptography.fernet import Fernet
import os

# Generate and save the encryption key (Run once and store the key securely, e.g., in environment variables)
def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

# Load the encryption key
def load_key():
    return open("secret.key", "rb").read()

# Encrypt sensitive data
def encrypt_data(data, key):
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data

# Decrypt sensitive data
def decrypt_data(encrypted_data, key):
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data).decode()
    return decrypted_data

# Initialize the database and create tables if not exist
def initialize_db():
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_token TEXT NOT NULL,
            last_four TEXT NOT NULL,
            expiration_date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Function to save card information (assuming card token is provided by a third-party service)
def save_payment_card(user_id, card_token, last_four, expiration_date):
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()

    # Encrypt card token before storing it
    key = load_key()
    encrypted_token = encrypt_data(card_token, key)

    # Insert card details into the database
    cursor.execute('''
        INSERT INTO payment_cards (user_id, card_token, last_four, expiration_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, encrypted_token, last_four, expiration_date))

    conn.commit()
    conn.close()

# Function to retrieve card information
def get_payment_card(user_id):
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()

    cursor.execute('SELECT card_token, last_four, expiration_date FROM payment_cards WHERE user_id = ?', (user_id,))
    card = cursor.fetchone()

    if card:
        encrypted_token, last_four, expiration_date = card
        key = load_key()
        card_token = decrypt_data(encrypted_token, key)
        return {
            'card_token': card_token,
            'last_four': last_four,
            'expiration_date': expiration_date
        }
    else:
        return None

# Test the functionality
if __name__ == "__main__":
    # Run once to generate the key
    generate_key()
    
    # Initialize the database and table
    initialize_db()
    
    # Sample user ID and card details (the card token would be received from a payment processor like Stripe)
    user_id = 1
    card_token = "tok_1HgfhjGJKShYh78"  # Placeholder token from a payment processor
    last_four = "1234"
    expiration_date = "12/25"

    # Save payment card
    save_payment_card(user_id, card_token, last_four, expiration_date)
    
    # Retrieve payment card details
    card_info = get_payment_card(user_id)
    if card_info:
        print(f"Card Token: {card_info['card_token']}")
        print(f"Last Four: {card_info['last_four']}")
        print(f"Expiration Date: {card_info['expiration_date']}")
    else:
        print("No card found for the user.")
