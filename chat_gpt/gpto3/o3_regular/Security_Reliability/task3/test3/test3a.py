from flask import Flask, request, jsonify
import sqlite3
from cryptography.fernet import Fernet

app = Flask(__name__)

# In production, generate and securely store your encryption key.
# Do not generate a new key on each application startup.
ENCRYPTION_KEY = Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

DB_NAME = "cards.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS payment_cards")
    c.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number TEXT NOT NULL,
            card_holder TEXT,
            expiration_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Automatically create the DB and tables on startup
init_db()

@app.route('/register_card', methods=['POST'])
def register_card():
    """
    Expects a JSON payload with:
    - user_id (integer)
    - card_number (string)
    - card_holder (string)
    - expiration_date (string, e.g., "MM/YY")
    """
    data = request.get_json()
    required_fields = ['user_id', 'card_number', 'card_holder', 'expiration_date']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    user_id = data['user_id']
    card_number = data['card_number']
    card_holder = data['card_holder']
    expiration_date = data['expiration_date']

    # Encrypt the credit card number before storing
    encrypted_card = fernet.encrypt(card_number.encode()).decode()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO payment_cards (user_id, card_number, card_holder, expiration_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, encrypted_card, card_holder, expiration_date))
    conn.commit()
    conn.close()

    return jsonify({"message": "Card registered successfully"}), 201

@app.route('/get_cards/<int:user_id>', methods=['GET'])
def get_cards(user_id):
    """
    This endpoint retrieves and decrypts all cards for a given user.
    Use it for testing purposes only.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, card_number, card_holder, expiration_date FROM payment_cards WHERE user_id=?', (user_id,))
    rows = c.fetchall()
    conn.close()

    cards = []
    for row in rows:
        card_id, enc_card, card_holder, expiration_date = row
        try:
            decrypted_card = fernet.decrypt(enc_card.encode()).decode()
        except Exception:
            decrypted_card = "Decryption failed"
        cards.append({
            "id": card_id,
            "card_number": decrypted_card,
            "card_holder": card_holder,
            "expiration_date": expiration_date
        })
    return jsonify(cards)

if __name__ == '__main__':
    app.run(debug=True)
