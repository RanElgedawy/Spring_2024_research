import sqlite3
import re
from datetime import datetime
from cryptography.fernet import Fernet

def validate_expiration_date(expiration_date):
    """
    Validates that the expiration date is in MM/YY format and is not in the past.
    
    Raises:
        ValueError: If the expiration date is not in the correct format or is in the past.
    """
    # Validate format: MM/YY (where MM is 01 to 12 and YY is two digits)
    pattern = r"^(0[1-9]|1[0-2])/(\d{2})$"
    match = re.match(pattern, expiration_date)
    if not match:
        raise ValueError("Expiration date must be in the format MM/YY.")
    
    month_str, year_str = match.groups()
    month = int(month_str)
    year = 2000 + int(year_str)  # Assumes the expiration year is in the 2000s

    now = datetime.now()
    # Assume the card is valid through the end of the expiration month.
    # Construct the first day of the following month.
    if month == 12:
        exp_threshold = datetime(year + 1, 1, 1)
    else:
        exp_threshold = datetime(year, month + 1, 1)
    
    if now >= exp_threshold:
        raise ValueError("The expiration date is in the past.")
    return True

class PaymentCardManager:
    def __init__(self, db_path, encryption_key):
        self.db_path = db_path
        self.fernet = Fernet(encryption_key)
        # Connect to SQLite database; if the file doesn't exist, it will be created.
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        """Automatically creates the payment_cards table if it doesn't exist."""
        with self.conn:
            self.conn.execute("DROP TABLE IF EXISTS payment_cards")
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS payment_cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    card_number BLOB NOT NULL,
                    cvv BLOB NOT NULL,
                    expiration_date TEXT NOT NULL,
                    card_holder_name TEXT NOT NULL,
                    billing_zip_code TEXT NOT NULL
                )
            ''')

    def add_card(self, user_id, card_number, cvv, expiration_date, card_holder_name, billing_zip_code):
        """
        Validates input parameters (including expiration date), encrypts sensitive information,
        and inserts a new payment card record.
        
        Expected parameters:
          - card_number: The credit card number.
          - cvv: The card verification value (CVV/CCV).
          - expiration_date: The card's expiration date in MM/YY format.
          - card_holder_name: The name on the card.
          - billing_zip_code: The billing ZIP code associated with the card.
        """
        # Verify that all required parameters are provided.
        if not all([card_number, cvv, expiration_date, card_holder_name, billing_zip_code]):
            raise ValueError("Missing one or more required input parameters: "
                             "card_number, cvv, expiration_date, card_holder_name, billing_zip_code")
        
        # Validate the expiration date.
        validate_expiration_date(expiration_date)
        
        # Encrypt sensitive data.
        encrypted_card_number = self.fernet.encrypt(card_number.encode('utf-8'))
        encrypted_cvv = self.fernet.encrypt(cvv.encode('utf-8'))
        
        with self.conn:
            self.conn.execute('''
                INSERT INTO payment_cards (user_id, card_number, cvv, expiration_date, card_holder_name, billing_zip_code)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, encrypted_card_number, encrypted_cvv, expiration_date, card_holder_name, billing_zip_code))
        print("Card successfully added for user:", user_id)

    def get_cards(self, user_id):
        """
        Retrieves and decrypts all payment cards for the given user.
        (Note: In a real-world scenario, sensitive fields such as CVV should typically not be retrieved.)
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, card_number, cvv, expiration_date, card_holder_name, billing_zip_code
            FROM payment_cards WHERE user_id = ?
        ''', (user_id,))
        cards = cursor.fetchall()
        result = []
        for card in cards:
            decrypted_card_number = self.fernet.decrypt(card[1]).decode('utf-8')
            decrypted_cvv = self.fernet.decrypt(card[2]).decode('utf-8')
            result.append({
                "id": card[0],
                "card_number": decrypted_card_number,
                "cvv": decrypted_cvv,
                "expiration_date": card[3],
                "card_holder_name": card[4],
                "billing_zip_code": card[5]
            })
        return result

if __name__ == "__main__":
    # In a real application, securely store and retrieve this key.
    key = Fernet.generate_key()
    
    # Initialize the payment card manager with the database file and encryption key.
    manager = PaymentCardManager("cards.db", key)
    
    # Example test: Add a payment card for user with ID 1.
    test_user_id = 1
    test_card_number = "4111111111111111"  # Example Visa test number.
    test_cvv = "123"
    test_expiration_date = "12/25"
    test_card_holder = "John Doe"
    test_billing_zip = "12345"
    
    try:
        print("Adding a test card...")
        manager.add_card(test_user_id, test_card_number, test_cvv, test_expiration_date, test_card_holder, test_billing_zip)
    except ValueError as e:
        print("Error:", e)
    
    # Retrieve and display stored cards for the test user.
    print("\nStored cards for user", test_user_id, ":")
    stored_cards = manager.get_cards(test_user_id)
    for card in stored_cards:
        print(card)
