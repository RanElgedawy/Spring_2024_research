import os
import sqlite3
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet

app = Flask(__name__)
DATABASE = 'cards.db'

# In production, store your encryption key securely.
# Here we generate a key for demonstration or read it from an environment variable.
KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
fernet = Fernet(KEY)

def init_db():
    """Initializes the database and creates the cards table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS cards")
    c.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            cardholder_name TEXT NOT NULL,
            card_number BLOB NOT NULL,
            expiration_date TEXT NOT NULL,
            cvv BLOB NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/register_card', methods=['POST'])
def register_card():
    """
    Registers a new payment card.
    Expected JSON payload:
    {
        "user_id": 1,
        "cardholder_name": "John Doe",
        "card_number": "4111111111111111",
        "expiration_date": "12/25",
        "cvv": "123"
    }
    """
    data = request.get_json()
    user_id = data.get('user_id')
    cardholder_name = data.get('cardholder_name')
    card_number = data.get('card_number')
    expiration_date = data.get('expiration_date')
    cvv = data.get('cvv')

    # Validate input
    if not all([user_id, cardholder_name, card_number, expiration_date, cvv]):
        return jsonify({'error': 'Missing fields'}), 400

    # Encrypt sensitive data
    encrypted_card_number = fernet.encrypt(card_number.encode())
    encrypted_cvv = fernet.encrypt(cvv.encode())

    # Insert data securely using parameterized queries to prevent SQL injection
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO cards (user_id, cardholder_name, card_number, expiration_date, cvv)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, cardholder_name, encrypted_card_number, expiration_date, encrypted_cvv))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Card registered successfully'}), 201

# This endpoint is provided for testing only.
# It decrypts and returns stored card details – DO NOT expose such functionality in production.
@app.route('/list_cards', methods=['GET'])
def list_cards():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, user_id, cardholder_name, card_number, expiration_date, cvv FROM cards')
    rows = c.fetchall()
    conn.close()

    cards = []
    for row in rows:
        card = {
            'id': row[0],
            'user_id': row[1],
            'cardholder_name': row[2],
            'card_number': fernet.decrypt(row[3]).decode(),
            'expiration_date': row[4],
            'cvv': fernet.decrypt(row[5]).decode()
        }
        cards.append(card)
    return jsonify(cards)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
