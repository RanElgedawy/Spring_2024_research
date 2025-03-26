#!/usr/bin/env python3
import os
import sqlite3
from cryptography.fernet import Fernet

# Load or generate encryption key
def load_key():
    # In production, ensure the key is stored securely (e.g., in an environment variable or secure vault)
    if os.path.exists("secret.key"):
        with open("secret.key", "rb") as key_file:
            key = key_file.read()
    else:
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)
    return key

KEY = load_key()
cipher_suite = Fernet(KEY)

# Connect to the SQLite database (will create if not exists)
DB_NAME = "cards.db"
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Create table for payment cards
def create_tables():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS payment_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        cardholder_name TEXT NOT NULL,
        encrypted_card_number TEXT NOT NULL,
        expiry_month INTEGER NOT NULL,
        expiry_year INTEGER NOT NULL,
        card_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute(create_table_query)
    conn.commit()

# Add a payment card for a user (encrypts the card number)
def add_payment_card(user_id, cardholder_name, card_number, expiry_month, expiry_year, card_type=None):
    encrypted_card_number = cipher_suite.encrypt(card_number.encode()).decode()
    insert_query = """
    INSERT INTO payment_cards (user_id, cardholder_name, encrypted_card_number, expiry_month, expiry_year, card_type)
    VALUES (?, ?, ?, ?, ?, ?);
    """
    cursor.execute(insert_query, (user_id, cardholder_name, encrypted_card_number, expiry_month, expiry_year, card_type))
    conn.commit()
    print("Payment card added successfully.")

# For testing: retrieve and decrypt payment cards for a user.
# In a real system, you generally avoid decrypting and exposing full card numbers.
def get_payment_cards(user_id):
    select_query = """
    SELECT id, user_id, cardholder_name, encrypted_card_number, expiry_month, expiry_year, card_type
    FROM payment_cards WHERE user_id = ?;
    """
    cursor.execute(select_query, (user_id,))
    rows = cursor.fetchall()
    cards = []
    for row in rows:
        try:
            decrypted_card_number = cipher_suite.decrypt(row[3].encode()).decode()
        except Exception:
            decrypted_card_number = "Decryption error"
        cards.append({
            "id": row[0],
            "user_id": row[1],
            "cardholder_name": row[2],
            "card_number": decrypted_card_number,
            "expiry_month": row[4],
            "expiry_year": row[5],
            "card_type": row[6]
        })
    return cards

# Main function to test the functionality
def main():
    create_tables()
    
    # Simulate a logged-in user (e.g., user_id = 1)
    user_id = 1
    print("Register a new payment card.")
    
    cardholder_name = input("Enter cardholder name: ")
    card_number = input("Enter card number (digits only, no spaces): ")
    expiry_month = int(input("Enter expiry month (MM): "))
    expiry_year = int(input("Enter expiry year (YYYY): "))
    card_type = input("Enter card type (e.g., Visa, MasterCard): ")
    
    add_payment_card(user_id, cardholder_name, card_number, expiry_month, expiry_year, card_type)
    
    # Retrieve and display stored cards for testing (decrypts card number)
    cards = get_payment_cards(user_id)
    print(f"\nStored Payment Cards for user_id {user_id}:")
    for card in cards:
        print(card)

if __name__ == "__main__":
    main()
