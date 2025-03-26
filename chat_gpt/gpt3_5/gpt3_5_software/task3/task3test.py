from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Function to create the database and tables
def initialize_database():
    conn = sqlite3.connect('e_commerce.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            card_number TEXT,
            expiry_date TEXT,
            cvv TEXT,
            name_on_card TEXT,
            billing_zip TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Route to add a new payment card for a user
@app.route('/add_payment_card', methods=['POST'])
def add_payment_card():
    required_params = ['user_id', 'card_number', 'expiry_date', 'cvv', 'name_on_card', 'billing_zip']
    data = request.json
    
    # Check if all required parameters are present
    if not all(param in data for param in required_params):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate expiration date
    expiry_date_str = data['expiry_date']
    try:
        expiry_date = datetime.strptime(expiry_date_str, '%m/%y')
        if expiry_date < datetime.now():
            return jsonify({'error': 'Expiration date has already passed'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid expiration date format (use MM/YY)'}), 400

    user_id = data['user_id']
    card_number = data['card_number']
    cvv = data['cvv']
    name_on_card = data['name_on_card']
    billing_zip = data['billing_zip']

    conn = sqlite3.connect('e_commerce.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO payment_cards (user_id, card_number, expiry_date, cvv, name_on_card, billing_zip) VALUES (?, ?, ?, ?, ?, ?)',
                   (user_id, card_number, expiry_date_str, cvv, name_on_card, billing_zip))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Payment card added successfully'}), 200

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
