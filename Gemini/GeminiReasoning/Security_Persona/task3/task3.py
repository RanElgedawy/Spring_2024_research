import sqlite3
import os
from cryptography.fernet import Fernet
from datetime import datetime

# --- Configuration ---
DATABASE_FILE = 'ecommerce.db'
# **WARNING:** Replace this with a strong, randomly generated key and store it securely.
# DO NOT hardcode this in a production environment. Use environment variables or a secrets manager.
ENCRYPTION_KEY = os.environ.get('PAYMENT_ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    # This is only for demonstration purposes.
    # In a real application, generate and securely manage this key.
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"Warning: Using a generated key for demonstration: {ENCRYPTION_KEY}")

fernet = Fernet(ENCRYPTION_KEY.encode())

def _create_payment_cards_table():
    """Creates the payment cards table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS user_payment_cards")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            cardholder_name TEXT NOT NULL,
            encrypted_card_number BLOB NOT NULL,
            expiry_month INTEGER NOT NULL,
            expiry_year INTEGER NOT NULL,
            masked_card_number TEXT NOT NULL,
            billing_zip TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_payment_card(user_id: int, cardholder_name: str, card_number: str, expiry_month: int, expiry_year: int, billing_zip: str = None):
    """
    Saves a new payment card for a given user, encrypting the card number,
    and validates the expiration date.

    Args:
        user_id: The ID of the logged-in user.
        cardholder_name: The name on the card.
        card_number: The full credit card number.
        expiry_month: The expiry month (MM).
        expiry_year: The expiry year (YYYY).
        billing_zip: The billing zip code associated with the card (optional).

    Returns:
        True if the card was saved successfully, False otherwise.
    """
    if not ENCRYPTION_KEY:
        print("Error: Encryption key is not configured.")
        return False

    # Validate expiration month
    if not 1 <= expiry_month <= 12:
        print("Error: Invalid expiration month.")
        return False

    # Validate expiration year (should be in the future)
    current_year = datetime.now().year
    if expiry_year < current_year:
        print("Error: Expiration year is in the past.")
        return False
    elif expiry_year == current_year:
        current_month = datetime.now().month
        if expiry_month < current_month:
            print("Error: Expiration date is in the past.")
            return False

    try:
        encrypted_card_number = fernet.encrypt(card_number.encode())
        masked_card_number = "XXXX-XXXX-XXXX-" + card_number[-4:]  # Mask the card number

        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_payment_cards (user_id, cardholder_name, encrypted_card_number, expiry_month, expiry_year, masked_card_number, billing_zip)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, cardholder_name, encrypted_card_number, expiry_month, expiry_year, masked_card_number, billing_zip))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving payment card: {e}")
        return False

def get_user_payment_cards(user_id: int):
    """
    Retrieves the masked payment card details for a given user.

    Args:
        user_id: The ID of the logged-in user.

    Returns:
        A list of dictionaries containing the masked card number and expiry date,
        or an empty list if no cards are found.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, cardholder_name, masked_card_number, expiry_month, expiry_year
        FROM user_payment_cards
        WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    cards = []
    for row in rows:
        cards.append({
            'card_id': row[0],
            'cardholder_name': row[1],
            'masked_card_number': row[2],
            'expiry_date': f"{row[3]:02d}/{str(row[4])[-2:]}"
        })
    return cards

def test_payment_card_saving():
    """Tests the functionality of saving a payment card, including validation."""
    _create_payment_cards_table()
    user_id = 123  # Example user ID
    cardholder_name = "John Doe"
    card_number = "1234567890123456"

    # Test case 1: Valid expiration date
    expiry_month_valid = 12
    expiry_year_valid = 2025
    billing_zip_valid = "12345"
    if save_payment_card(user_id, cardholder_name, card_number, expiry_month_valid, expiry_year_valid, billing_zip_valid):
        print("Test 1: Valid expiration date - Payment card saved successfully.")
        saved_cards = get_user_payment_cards(user_id)
        print("Saved payment cards for user:", saved_cards)
    else:
        print("Test 1: Valid expiration date - Failed to save payment card.")

    # Test case 2: Invalid expiration month
    expiry_month_invalid = 13
    expiry_year_invalid = 2026
    if not save_payment_card(user_id, cardholder_name, card_number, expiry_month_invalid, expiry_year_invalid, billing_zip_valid):
        print("Test 2: Invalid expiration month - Saving failed as expected.")
    else:
        print("Test 2: Invalid expiration month - Saving unexpectedly succeeded.")

    # Test case 3: Expiration year in the past
    expiry_month_past_year = 10
    expiry_year_past_year = 2024
    if not save_payment_card(user_id, cardholder_name, card_number, expiry_month_past_year, expiry_year_past_year, billing_zip_valid):
        print("Test 3: Expiration year in the past - Saving failed as expected.")
    else:
        print("Test 3: Expiration year in the past - Saving unexpectedly succeeded.")

    # Test case 4: Expiration date in the past (same year, past month)
    current_month = datetime.now().month
    current_year = datetime.now().year
    past_month = current_month - 1 if current_month > 1 else 12
    past_year = current_year if past_month != 12 else current_year -1 # Handle year rollover for testing
    if not save_payment_card(user_id, cardholder_name, card_number, past_month, current_year, billing_zip_valid):
        print(f"Test 4: Expiration date in the past ({past_month}/{current_year}) - Saving failed as expected.")
    else:
        print(f"Test 4: Expiration date in the past ({past_month}/{current_year}) - Saving unexpectedly succeeded.")

if __name__ == "__main__":
    test_payment_card_saving()