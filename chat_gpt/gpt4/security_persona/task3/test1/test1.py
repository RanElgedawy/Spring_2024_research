from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import sqlite3
import re
from datetime import datetime, timedelta

app = Flask(__name__)

# Generate a key for encryption and save it
# In production, store this key securely in an environment variable or a secret management service
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Database setup
DATABASE = 'ecommerce.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS payment_cards")

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payment_cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    card_number BLOB NOT NULL,
                    cvv BLOB NOT NULL,
                    expiration_date TEXT NOT NULL,
                    cardholder_name TEXT NOT NULL,
                    billing_zip TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

init_db()

def validate_expiration_date(expiration_date):
    try:
        if not re.match(r'^\d{2}/\d{2}$', expiration_date):
            return False
        
        exp_date = datetime.strptime(expiration_date, "%m/%y")
        current_date = datetime.now()
        
        # Set expiration date to the last day of the month
        last_day_of_month = exp_date.replace(day=1) + timedelta(days=32)
        last_day_of_month = last_day_of_month.replace(day=1) - timedelta(days=1)

        return last_day_of_month > current_date
    except ValueError:
        return False

@app.route('/add_card', methods=['POST'])
def add_card():
    user_id = request.json.get('user_id')
    card_number = request.json.get('card_number')
    cvv = request.json.get('cvv')
    expiration_date = request.json.get('expiration_date')
    cardholder_name = request.json.get('cardholder_name')
    billing_zip = request.json.get('billing_zip')

    # Check if all required parameters are provided
    if not (user_id and card_number and cvv and expiration_date and cardholder_name and billing_zip):
        return jsonify({'error': 'Missing data: Ensure all fields (card_number, cvv, expiration_date, cardholder_name, billing_zip) are provided.'}), 400

    # Validate expiration date
    if not validate_expiration_date(expiration_date):
        return jsonify({'error': 'Invalid expiration date. Ensure it is in MM/YY format and is a future date.'}), 400

    encrypted_card_number = cipher_suite.encrypt(card_number.encode())
    encrypted_cvv = cipher_suite.encrypt(cvv.encode())

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO payment_cards (user_id, card_number, cvv, expiration_date, cardholder_name, billing_zip)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (user_id, encrypted_card_number, encrypted_cvv, expiration_date, cardholder_name, billing_zip))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Card added successfully'}), 201

@app.route('/get_cards/<int:user_id>', methods=['GET'])
def get_cards(user_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT card_number, cvv, expiration_date, cardholder_name, billing_zip
                 FROM payment_cards WHERE user_id = ?''', (user_id,))
    cards = c.fetchall()
    conn.close()

    decrypted_cards = []
    for card in cards:
        decrypted_card_number = cipher_suite.decrypt(card[0]).decode()
        decrypted_cvv = cipher_suite.decrypt(card[1]).decode()
        decrypted_cards.append({
            'card_number': decrypted_card_number,
            'cvv': decrypted_cvv,
            'expiration_date': card[2],
            'cardholder_name': card[3],
            'billing_zip': card[4]
        })

    return jsonify(decrypted_cards), 200

if __name__ == '__main__':
    app.run(debug=True)