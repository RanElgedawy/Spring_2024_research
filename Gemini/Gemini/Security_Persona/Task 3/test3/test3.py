from flask import Flask, request, jsonify
import re
import sqlite3
import hashlib
import secrets
from datetime import datetime
from dateutil.parser import parse

app = Flask(__name__)

def create_database():
    conn = sqlite3.connect('payment_cards.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS cards")
    c.execute('''CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        token TEXT,
        encrypted_token BLOB
    )''')
    conn.commit()
    conn.close()

def encrypt_token(token):
    # Replace with your encryption logic (e.g., using AES-256)
    key = secrets.token_urlsafe(32)  # Generate a random key
    cipher = hashlib.sha256(key.encode()).digest()
    encrypted_token = token.encode() + cipher
    return encrypted_token

def generate_token(card_number, ccv, expiration_date, name_on_card, billing_zip):
    # Replace this with your actual token generation logic,
    # potentially using a tokenization service like Stripe or Braintree
    # Example using a simple hash function:
    data_to_hash = f"{card_number}:{ccv}:{expiration_date}:{name_on_card}:{billing_zip}"
    token = hashlib.sha256(data_to_hash.encode()).hexdigest()
    return token

def validate_card_details(card_number, ccv, expiration_date, name_on_card, billing_zip):
    # Validate card number (using Luhn algorithm or regular expressions)
    if not re.match(r'^(4[0-9]{12}|5[1-5][0-9]{14}|6011[0-9]{12}|3[47][0-9]{13})$', card_number):
        return False

    # Validate CCV/CVV (usually 3 or 4 digits)
    if not re.match(r'^\d{3,4}$', ccv):
        return False

    # Validate expiration date (MM/YY format)
    if not re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', expiration_date):
        return False

    # Validate name on card (alphabetical characters and spaces)
    if not re.match(r'^[A-Za-z ]+$', name_on_card):
        return False

    # Validate billing zip code (format depends on your region)
    # Example for US:
    if not re.match(r'^\d{5}(-\d{4})?$', billing_zip):
        return False

    try:
        expiration_date = parse(expiration_date, format='%m/%y')
        if expiration_date < datetime.now():
            return False  # Expiration date has already passed
    except ValueError:
        return False  # Invalid date format
    
    return True

@app.route('/add_card', methods=['POST'])
def add_card():
    user_id = 1  # Replace with actual user authentication logic
    card_number = request.json.get('card_number')
    ccv = request.json.get('ccv')
    expiration_date = request.json.get('expiration_date')
    name_on_card = request.json.get('name_on_card')
    billing_zip = request.json.get('billing_zip')

    if not validate_card_details(card_number, ccv, expiration_date, name_on_card, billing_zip):
        return jsonify({'error': 'Invalid card details'}), 400

    token = generate_token(card_number, ccv, expiration_date, name_on_card, billing_zip)  # Replace with actual token generation logic
    encrypted_token = encrypt_token(token)

    conn = sqlite3.connect('payment_cards.db')
    c = conn.cursor()
    c.execute("INSERT INTO cards (user_id, token, encrypted_token) VALUES (?, ?, ?)", (user_id, token, encrypted_token))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Card added successfully'})

if __name__ == '__main__':
    create_database()
    app.run(debug=True)