import sqlite3
from cryptography.fernet import Fernet

# In production, store this key securely (e.g., in an environment variable or secure key vault)
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

def init_db(db_name='ecommerce.db'):
    """Initializes the SQLite database and creates the payment_cards table if it doesn't exist."""
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS payment_cards")
    c.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number BLOB NOT NULL,
            expiration_date TEXT NOT NULL,
            card_holder_name TEXT
        )
    ''')
    conn.commit()
    return conn

def store_payment_card(conn, user_id, card_number, expiration_date, card_holder_name=None):
    """
    Encrypts the card number and stores the payment card information in the database.
    
    Args:
        conn: SQLite connection object.
        user_id: The ID of the logged-in user.
        card_number: The plaintext credit card number.
        expiration_date: The card's expiration date (e.g., "12/24").
        card_holder_name: (Optional) The name on the card.
    """
    # Encrypt the card number
    encrypted_card = cipher_suite.encrypt(card_number.encode())
    c = conn.cursor()
    c.execute('''
        INSERT INTO payment_cards (user_id, card_number, expiration_date, card_holder_name)
        VALUES (?, ?, ?, ?)
    ''', (user_id, encrypted_card, expiration_date, card_holder_name))
    conn.commit()

def get_payment_cards(conn, user_id):
    """
    Retrieves and decrypts all payment cards for a given user.
    
    Args:
        conn: SQLite connection object.
        user_id: The ID of the user whose cards will be retrieved.
    
    Returns:
        A list of dictionaries containing the card details.
    """
    c = conn.cursor()
    c.execute('''
        SELECT id, card_number, expiration_date, card_holder_name FROM payment_cards
        WHERE user_id = ?
    ''', (user_id,))
    rows = c.fetchall()
    cards = []
    for row in rows:
        decrypted_card = cipher_suite.decrypt(row[1]).decode()
        cards.append({
            "id": row[0],
            "card_number": decrypted_card,
            "expiration_date": row[2],
            "card_holder_name": row[3]
        })
    return cards

def test_functionality():
    """Function to test storing and retrieving a payment card."""
    conn = init_db()
    test_user_id = 1
    test_card_number = "4111111111111111"
    test_expiration = "12/24"
    test_holder = "John Doe"
    
    store_payment_card(conn, test_user_id, test_card_number, test_expiration, test_holder)
    
    print("Stored payment cards for user:", test_user_id)
    cards = get_payment_cards(conn, test_user_id)
    for card in cards:
        print(card)

if __name__ == '__main__':
    test_functionality()
