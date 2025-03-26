from flask import Flask, request, jsonify
import sqlite3
import datetime
import os
import random
import string

app = Flask(__name__)

# Create database if it doesn't exist
def create_database():
    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS Users")
    c.execute("DROP TABLE IF EXISTS PaymentTokens")

    c.execute('''CREATE TABLE IF NOT EXISTS Users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 email TEXT UNIQUE,
                 password TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS PaymentTokens (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 token TEXT UNIQUE,
                 user_id INTEGER,
                 created_at TEXT,
                 FOREIGN KEY (user_id) REFERENCES Users(id)
                 )''')
    
    c.execute("INSERT INTO Users (email, password) VALUES (?, ?)", ('testuser@example.com', 'password123'))

    conn.commit()
    conn.close()

def generate_token():
    """Generates a random token for testing purposes."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

def validate_expiration_date(expiration_date):
    try:
        # Parse the expiration date in the format "YYYY-MM"
        expiration_year, expiration_month = expiration_date.split('-')
        expiration_year = int(expiration_year)
        expiration_month = int(expiration_month)

        # Check if the expiration date is in the future
        current_date = datetime.datetime.now()
        return expiration_year > current_date.year or (expiration_year == current_date.year and expiration_month >= current_date.month)
    except ValueError:
        # Handle invalid expiration date format
        return False
    
# Example function to handle card registration using a payment gateway
def register_card(user_id, card_data):
    required_fields = ['card_number', 'ccv', 'expiration_date', 'name_on_card', 'billing_zip_code']
    for field in required_fields:
        if field not in card_data:
            raise ValueError(f"Missing required field: {field}")    # Replace with actual payment gateway integration
    
    # Validate expiration date
    if not validate_expiration_date(card_data['expiration_date']):
        raise ValueError("Invalid expiration date")
    
    token = generate_token()
    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute("INSERT INTO PaymentTokens (token, user_id, created_at) VALUES (?, ?, ?)", (token, user_id, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    return token

# Flask route to handle card registration requests
@app.route('/register-card', methods=['POST'])
def register_card_endpoint():
    user_id = request.json['user_id']
    card_data = request.json['card_data']
    token = register_card(user_id, card_data)
    return jsonify({'token': token})

if __name__ == '__main__':
    create_database()
    app.run(debug=True)