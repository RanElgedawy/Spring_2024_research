from flask import Flask, request, jsonify
import sqlite3
from cryptography.fernet import Fernet
import base64
import os
import datetime
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(filename='error.log'),
                        logging.StreamHandler()
                    ])

# Generate a random 32-byte key for Fernet encryption
def generate_secret_key():
    return base64.urlsafe_b64encode(os.urandom(32))

# Store the generated key as a global variable
SECRET_KEY = generate_secret_key()

# Initialize Fernet cipher
cipher_suite = Fernet(SECRET_KEY)

# Initialize database
conn = sqlite3.connect('payment.db')
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS users")
c.execute("DROP TABLE IF EXISTS payment_cards")

# Create table for users
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL,
              password TEXT NOT NULL)''')

c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("test", "test"))
# Create table for payment cards
c.execute('''CREATE TABLE IF NOT EXISTS payment_cards
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              card_number TEXT NOT NULL,
              encrypted_cvv TEXT NOT NULL)''')

# Save changes and close connection
conn.commit()
conn.close()

# Encrypt and decrypt functions
def encrypt(data):
    key = app.secret_key
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt(data):
    key = app.secret_key
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(data.encode()).decode()

# Function to validate expiration date
def validate_expiration_date(expiration_date):
    try:
        # Parse the expiration date string to a datetime object
        expiration_date = datetime.datetime.strptime(expiration_date, '%m/%Y')  # Use datetime.datetime.strptime()
        # Check if the expiration date is in the future
        return expiration_date > datetime.datetime.now()  # Use datetime.datetime.now()
    except ValueError:
        return False

# Routes
@app.route('/register_card', methods=['POST'])
def register_card():
    data = request.get_json()

    # Check if all expected parameters are present
    expected_params = ['user_id', 'card_number', 'cvv', 'expiration_date', 'name_on_card', 'billing_zip']
    if not all(param in data for param in expected_params):
        logging.error('Missing input parameters')
        return jsonify({'error': 'Missing input parameters'}), 400

    user_id = data.get('user_id')
    card_number = data.get('card_number')
    cvv = data.get('cvv')
    expiration_date = data.get('expiration_date')
    name_on_card = data.get('name_on_card')
    billing_zip = data.get('billing_zip')

    # Validate expiration date
    if not validate_expiration_date(expiration_date):
        logging.error('Invalid expiration date')
        return jsonify({'error': 'Invalid expiration date'}), 400

    # Check if the provided user ID exists
    conn = sqlite3.connect('payment.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()

    if not user:
        logging.error('Invalid user ID')
        return jsonify({'error': 'Invalid user ID'}), 400

    # Check if cvv is provided and not empty
    if cvv is None or not cvv.strip():
        logging.error('CVV is missing or empty')
        return jsonify({'error': 'CVV is missing or empty'}), 400


    try:
        # Encrypt CVV before storing
        encrypted_cvv = encrypt(cvv)
    except Exception as e:
        error_message = f'Error encrypting CVV: {str(e)}'
        logging.error(error_message)
        return jsonify({'error': error_message}), 500

    try:
        # Save card details to database
        conn = sqlite3.connect('payment.db')
        c = conn.cursor()
        c.execute('''INSERT INTO payment_cards (user_id, card_number, encrypted_cvv)
                     VALUES (?, ?, ?)''', (user_id, card_number, encrypted_cvv))
        conn.commit()
        conn.close()
    except Exception as e:
        error_message = f'Error saving card details: {str(e)}'
        logging.error(error_message)
        return jsonify({'error': error_message}), 500

    return jsonify({'message': 'Payment card registered successfully'})

if __name__ == '__main__':
    app.run(debug=True)