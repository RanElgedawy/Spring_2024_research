from flask import Flask, request, jsonify
import sqlite3
from sqlite3 import Error
from datetime import datetime

app = Flask(__name__)

# Function to create a database connection
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

conn = create_connection("payment_cards.db")
with conn:
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS cards")
# Function to validate the expiration date
def validate_expiry_date(expiry_date):
    try:
        expiry_date = datetime.strptime(expiry_date, "%m/%y")
        current_date = datetime.now()
        if expiry_date < current_date:
            return False
        return True
    except ValueError:
        return False

# Function to create a new card
@app.route('/register_card', methods=['POST'])
def register_card():
    data = request.get_json()
    required_fields = ['user_id', 'card_number', 'expiry_date', 'cvv', 'name_on_card', 'billing_zip_code']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field "{field}" in request'}), 400
    
    user_id = data['user_id']
    card_number = data['card_number']
    expiry_date = data['expiry_date']
    cvv = data['cvv']
    name_on_card = data['name_on_card']
    billing_zip_code = data['billing_zip_code']
    
    if not all(isinstance(data[field], str) for field in ['card_number', 'expiry_date', 'cvv', 'name_on_card', 'billing_zip_code']):
        return jsonify({'error': 'Invalid data types in request'}), 400
    
    if not validate_expiry_date(expiry_date):
        return jsonify({'error': 'Invalid expiration date or card has expired'}), 400
    
    conn = create_connection("payment_cards.db")
    with conn:
        cur = conn.cursor()
        try:
            cur.execute("CREATE TABLE IF NOT EXISTS cards (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, card_number TEXT, expiry_date TEXT, cvv TEXT, name_on_card TEXT, billing_zip_code TEXT)")
            cur.execute("INSERT INTO cards (user_id, card_number, expiry_date, cvv, name_on_card, billing_zip_code) VALUES (?, ?, ?, ?, ?, ?)", (user_id, card_number, expiry_date, cvv, name_on_card, billing_zip_code))
            conn.commit()
            return jsonify({'message': 'Card registered successfully'}), 201
        except Error as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)