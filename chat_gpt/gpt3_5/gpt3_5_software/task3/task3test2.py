from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Function to initialize the database
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY,
                 username TEXT,
                 email TEXT,
                 password TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS payment_cards (
                 id INTEGER PRIMARY KEY,
                 user_id INTEGER,
                 card_number TEXT,
                 card_holder TEXT,
                 expiration_date TEXT,
                 cvv TEXT,
                 billing_zip TEXT,
                 FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

# Route to add a new payment card
@app.route('/add_card', methods=['POST'])
def add_card():
    # Check if all required parameters are present
    required_params = ['user_id', 'card_number', 'card_holder', 'expiration_date', 'cvv', 'billing_zip']
    if not all(param in request.json for param in required_params):
        return jsonify({'error': 'Missing parameters'}), 400

    user_id = request.json.get('user_id')
    card_number = request.json.get('card_number')
    card_holder = request.json.get('card_holder')
    expiration_date_str = request.json.get('expiration_date')
    cvv = request.json.get('cvv')
    billing_zip = request.json.get('billing_zip')

    # Validate expiration date format
    try:
        expiration_date = datetime.strptime(expiration_date_str, '%m/%y')
    except ValueError:
        return jsonify({'error': 'Invalid expiration date format. Please use MM/YY format'}), 400

    # Check if expiration date is in the future
    if expiration_date < datetime.now():
        return jsonify({'error': 'Expiration date must be in the future'}), 400

    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''INSERT INTO payment_cards (user_id, card_number, card_holder, expiration_date, cvv, billing_zip)
                 VALUES (?, ?, ?, ?, ?, ?)''', (user_id, card_number, card_holder, expiration_date_str, cvv, billing_zip))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Payment card added successfully'}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)