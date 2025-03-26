import os
from flask import Flask, request, jsonify
import sqlite3
from cryptography.fernet import Fernet
import datetime
import re

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')  # Set this in production!
fernet = Fernet.generate_key() if not app.config['SECRET_KEY'] else Fernet(app.config['SECRET_KEY'].encode())

# Database setup
DATABASE = 'payment_cards.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Add this line
    conn.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            encrypted_card BLOB NOT NULL,
            last_four CHAR(4) NOT NULL,
            encrypted_cvv BLOB NOT NULL,
            exp_month INTEGER NOT NULL,
            exp_year INTEGER NOT NULL,
            cardholder TEXT NOT NULL,
            encrypted_zip BLOB NOT NULL,
            last_four_zip CHAR(4) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    return conn

def validate_card(number):
    """Luhn algorithm validation"""
    number = str(number).replace(' ', '')
    if not number.isdigit() or len(number) < 13 or len(number) > 19:
        return False
    
    digits = list(map(int, number))
    checksum = sum(digits[-1::-2])
    checksum += sum([sum(divmod(d * 2, 10)) for d in digits[-2::-2]])
    return checksum % 10 == 0

@app.route('/cards', methods=['POST'])
def add_card():
    data = request.get_json()
    required = ['user_id', 'card_number', 'cvv', 'exp_month', 'exp_year', 'cardholder', 'billing_zip']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate card number
    card_number = data['card_number'].replace(' ', '')
    if not validate_card(card_number):
        return jsonify({'error': 'Invalid card number'}), 400

    # Validate CVV
    cvv = str(data['cvv']).strip()
    if not (len(cvv) in (3, 4) and cvv.isdigit()):
        return jsonify({'error': 'Invalid CVV'}), 400

    # Validate expiration date
    now = datetime.datetime.now()
    try:
        exp_month = int(data['exp_month'])
        exp_year = int(data['exp_year'])
        if not (1 <= exp_month <= 12):
            raise ValueError
        if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
            return jsonify({'error': 'Card expired'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid expiration date'}), 400

    # Validate billing zip
    billing_zip = re.sub(r'[^0-9]', '', str(data['billing_zip']))
    if len(billing_zip) < 5:
        return jsonify({'error': 'Invalid ZIP code'}), 400

    try:
        # Encrypt sensitive data
        encrypted_card = Fernet(fernet).encrypt(card_number.encode())
        encrypted_cvv = Fernet(fernet).encrypt(cvv.encode())  # Only for temporary validation
        encrypted_zip = Fernet(fernet).encrypt(billing_zip.encode())

        conn = get_db()
        conn.execute('''
            INSERT INTO payment_cards 
            (user_id, encrypted_card, last_four, encrypted_cvv, exp_month, exp_year, cardholder, encrypted_zip, last_four_zip)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['user_id'],
            encrypted_card,
            card_number[-4:],
            encrypted_cvv,
            exp_month,
            exp_year,
            data['cardholder'].strip(),
            encrypted_zip,
            billing_zip[-4:]
        ))
        conn.commit()
        return jsonify({'message': 'Card stored securely'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/cards/<int:user_id>', methods=['GET'])
def get_cards(user_id):
    try:
        conn = get_db()
        conn.row_factory = sqlite3.Row  # Add this line
        cur = conn.execute('''
            SELECT last_four, exp_month, exp_year, cardholder, created_at, last_four_zip 
            FROM payment_cards WHERE user_id =?
        ''', (user_id,))
        rows = cur.fetchall()
        return jsonify([dict(row) for row in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)