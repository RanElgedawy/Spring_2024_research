import os
import sqlite3
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet

app = Flask(__name__)
DATABASE = 'cards.db'

# In production, store your encryption key securely (e.g. in an environment variable or a key management system)
if 'ENCRYPTION_KEY' in os.environ:
    ENCRYPTION_KEY = os.environ['ENCRYPTION_KEY'].encode()
else:
    # For demonstration purposes only – do not use a randomly generated key in production!
    ENCRYPTION_KEY = Fernet.generate_key()
    print("WARNING: Using a generated encryption key for demonstration purposes. "
          "In production, use a persistent and secure key.")

fernet = Fernet(ENCRYPTION_KEY)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the payment_cards table if it does not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            card_number BLOB NOT NULL,
            expiration_date TEXT NOT NULL,
            cardholder_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/add_card', methods=['POST'])
def add_card():
    """
    Expects a JSON payload with:
      - user_id
      - card_number
      - expiration_date (e.g. "12/24")
      - cardholder_name
    The credit card number is encrypted before storage.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    card_number = data.get('card_number')
    expiration_date = data.get('expiration_date')
    cardholder_name = data.get('cardholder_name')
    
    # Basic input validation
    if not all([user_id, card_number, expiration_date, cardholder_name]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Encrypt the card number
    encrypted_card = fernet.encrypt(card_number.encode())
    
    # Save to the database using parameterized queries
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payment_cards (user_id, card_number, expiration_date, cardholder_name)
        VALUES (?, ?, ?, ?)
    ''', (user_id, encrypted_card, expiration_date, cardholder_name))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Payment card added successfully'}), 201

@app.route('/list_cards', methods=['GET'])
def list_cards():
    """
    For testing purposes only: retrieves all stored cards
    and decrypts the card numbers. In a real system, you likely
    would not return decrypted credit card numbers in an API.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM payment_cards')
    rows = cursor.fetchall()
    conn.close()
    
    cards = []
    for row in rows:
        try:
            decrypted_card = fernet.decrypt(row['card_number']).decode()
        except Exception as e:
            decrypted_card = "Error decrypting card"
        cards.append({
            'id': row['id'],
            'user_id': row['user_id'],
            'card_number': decrypted_card,
            'expiration_date': row['expiration_date'],
            'cardholder_name': row['cardholder_name'],
            'created_at': row['created_at']
        })
    
    return jsonify(cards)

if __name__ == '__main__':
    init_db()
    print("Server running... Use /add_card to add a card and /list_cards to view stored cards (testing only).")
    app.run(debug=True)
