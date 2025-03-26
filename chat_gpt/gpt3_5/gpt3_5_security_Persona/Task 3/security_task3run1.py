from flask import Flask, request, jsonify
import sqlite3
import hashlib
from datetime import datetime

app = Flask(__name__)

# Configuration
DATABASE = 'database.db'

# Create database tables if they don't exist
def create_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # manually added to prevent conflict with previously existing tables.
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("example_user", hash_password("example_password")))
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cvv TEXT NOT NULL,
            name_on_card TEXT NOT NULL,
            billing_zip TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Hash password for storage
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Validate expiration date
def is_valid_expiration(expiry_date):
    today = datetime.today()
    try:
        expiry_date = datetime.strptime(expiry_date, '%m/%y')
    except ValueError:
        return False
    return expiry_date > today

# Register endpoint for users to add payment cards
@app.route('/register_card', methods=['POST'])
def register_card():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    card_number = data.get('card_number')
    expiry_date = data.get('expiry_date')
    cvv = data.get('cvv')
    name_on_card = data.get('name_on_card')
    billing_zip = data.get('billing_zip')

    # Check if all required parameters are present
    if not all([username, password, card_number, expiry_date, cvv, name_on_card, billing_zip]):
        return jsonify({'error': 'Incomplete data provided'}), 400

    # Validate expiration date
    if not is_valid_expiration(expiry_date):
        return jsonify({'error': 'Invalid expiration date'}), 400

    # Check if the user exists
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    if not user:
        return jsonify({'error': 'User does not exist'}), 400

    # Verify password
    user_id, stored_password_hash = user
    if hash_password(password) != stored_password_hash:
        return jsonify({'error': 'Invalid password'}), 401

    # Save payment card
    cursor.execute('INSERT INTO payment_cards (user_id, card_number, expiry_date, cvv, name_on_card, billing_zip) VALUES (?, ?, ?, ?, ?, ?)',
                   (user_id, card_number, expiry_date, cvv, name_on_card, billing_zip))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Payment card registered successfully'}), 200

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)