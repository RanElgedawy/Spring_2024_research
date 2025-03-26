from flask import Flask, request, jsonify
import sqlite3
from cryptography.fernet import Fernet

app = Flask(__name__)
DB_NAME = "cards.db"

# In production, generate your key once and store it securely (e.g., in an environment variable)
ENCRYPTION_KEY = Fernet.generate_key()
cipher = Fernet(ENCRYPTION_KEY)

def init_db():
    """Initialize the SQLite database and create the payment_cards table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_holder TEXT,
            card_number TEXT,
            expiration_date TEXT,
            billing_address TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/add_card', methods=['POST'])
def add_card():
    """
    Expects JSON payload with:
      - user_id (assumed to be provided since the user is logged in)
      - card_holder
      - card_number
      - expiration_date
      - billing_address (optional)
      
    The card_number is encrypted before being stored.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    card_holder = data.get('card_holder')
    card_number = data.get('card_number')
    expiration_date = data.get('expiration_date')
    billing_address = data.get('billing_address', '')

    # Validate required fields
    if not all([user_id, card_holder, card_number, expiration_date]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Encrypt the card number before storing
    encrypted_card_number = cipher.encrypt(card_number.encode()).decode()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payment_cards (user_id, card_holder, card_number, expiration_date, billing_address)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, card_holder, encrypted_card_number, expiration_date, billing_address))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Card added successfully'}), 201

@app.route('/cards', methods=['GET'])
def list_cards():
    """
    For testing purposes only, this endpoint retrieves all cards from the database and decrypts
    the card numbers. In a real-world application, you would not expose decrypted sensitive data.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, card_holder, card_number, expiration_date, billing_address FROM payment_cards')
    rows = cursor.fetchall()
    conn.close()

    cards = []
    for row in rows:
        id, user_id, card_holder, encrypted_card_number, expiration_date, billing_address = row
        try:
            decrypted_card_number = cipher.decrypt(encrypted_card_number.encode()).decode()
        except Exception:
            decrypted_card_number = "Decryption Error"
        cards.append({
            'id': id,
            'user_id': user_id,
            'card_holder': card_holder,
            'card_number': decrypted_card_number,
            'expiration_date': expiration_date,
            'billing_address': billing_address
        })

    return jsonify(cards)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
