from flask import Flask, request, jsonify
import sqlite3
from cryptography.fernet import Fernet

app = Flask(__name__)

# Generate a new encryption key. In a real app, store and manage this securely.
encryption_key = Fernet.generate_key()
cipher = Fernet(encryption_key)

DATABASE = 'cards.db'

def init_db():
    """Initialize the SQLite database and create the payment_cards table if it doesn't exist."""
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS payment_cards")
        c.execute('''
            CREATE TABLE IF NOT EXISTS payment_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_number BLOB NOT NULL,
                expiration_date TEXT NOT NULL,
                cardholder_name TEXT NOT NULL
            )
        ''')
        conn.commit()

@app.route('/register_card', methods=['POST'])
def register_card():
    """
    Register a new payment card.
    Expects JSON with:
    - user_id (int)
    - card_number (string)
    - expiration_date (string, e.g., "12/26")
    - cardholder_name (string)
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    # Validate required fields
    required_fields = ['user_id', 'card_number', 'expiration_date', 'cardholder_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    # Encrypt the card number before storing
    encrypted_card_number = cipher.encrypt(data['card_number'].encode())

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO payment_cards (user_id, card_number, expiration_date, cardholder_name)
            VALUES (?, ?, ?, ?)
        ''', (data['user_id'], encrypted_card_number, data['expiration_date'], data['cardholder_name']))
        conn.commit()

    return jsonify({'message': 'Card registered successfully'}), 201

# For testing purposes only: Retrieve and display stored card details with decrypted card numbers.
@app.route('/cards', methods=['GET'])
def get_cards():
    """Retrieve all stored payment cards (decrypted for testing only)."""
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM payment_cards')
        rows = c.fetchall()
        cards = []
        for row in rows:
            try:
                decrypted_card = cipher.decrypt(row['card_number']).decode()
            except Exception:
                decrypted_card = 'Decryption error'
            cards.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'card_number': decrypted_card,
                'expiration_date': row['expiration_date'],
                'cardholder_name': row['cardholder_name']
            })
    return jsonify(cards), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
