import sqlite3
import os
from cryptography.fernet import Fernet

# In a real application, store the key securely (e.g., in an environment variable or key management system).
# Here we generate a key on the fly for demonstration purposes.
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

DATABASE_FILE = "payment_cards.db"

def setup_database():
    """Creates the payment_cards table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_encrypted TEXT NOT NULL,
            card_last4 TEXT NOT NULL,
            exp_month INTEGER NOT NULL,
            exp_year INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_payment_card(user_id, card_number, exp_month, exp_year):
    """
    Encrypts and stores the credit card information.
    
    Note: Do not store CVV as per PCI guidelines.
    We also store the last 4 digits (in plaintext) for display/reference.
    """
    # Encrypt the full card number
    encrypted_card = cipher_suite.encrypt(card_number.encode()).decode()
    card_last4 = card_number[-4:]
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payment_cards (user_id, card_encrypted, card_last4, exp_month, exp_year)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, encrypted_card, card_last4, exp_month, exp_year))
    conn.commit()
    conn.close()
    print("Payment card added successfully.")

def get_payment_cards(user_id):
    """
    Retrieves and decrypts all stored payment cards for a given user.
    Note: Decrypting full card numbers is generally not advised unless absolutely required.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, card_encrypted, card_last4, exp_month, exp_year
        FROM payment_cards WHERE user_id = ?
    ''', (user_id,))
    cards = cursor.fetchall()
    conn.close()
    
    results = []
    for card in cards:
        card_id, encrypted_card, card_last4, exp_month, exp_year = card
        try:
            decrypted_card = cipher_suite.decrypt(encrypted_card.encode()).decode()
        except Exception as e:
            decrypted_card = "Decryption error"
        results.append({
            "id": card_id,
            "card_number": decrypted_card,
            "card_last4": card_last4,
            "exp_month": exp_month,
            "exp_year": exp_year
        })
    return results

def test_functionality():
    setup_database()
    print("Database and table setup complete.")
    
    # Test data: Assume user with id 1 is logged in.
    user_id = 1
    print("\nAdding test payment cards...")
    add_payment_card(user_id, "4111111111111111", 12, 2026)
    add_payment_card(user_id, "5500000000000004", 11, 2025)
    
    print("\nRetrieving payment cards for user_id =", user_id)
    cards = get_payment_cards(user_id)
    for card in cards:
        print(f"Card ID: {card['id']}")
        print(f"Full Card Number: {card['card_number']}")
        print(f"Card Last 4: {card['card_last4']}")
        print(f"Expiration: {card['exp_month']:02d}/{card['exp_year']}")
        print("-" * 30)

if __name__ == "__main__":
    test_functionality()
