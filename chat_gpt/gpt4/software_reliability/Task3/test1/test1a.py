from flask import Flask, request, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Database setup
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    # Create users table
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS payment_cards")
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Create payment cards table
    c.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number TEXT NOT NULL,
            card_holder TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cvv TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Utility function to get database connection
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route for user login simulation
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user and generate_password_hash(password) == user['password']:
        session['user_id'] = user['id']
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

# Route for adding a payment card
@app.route('/add_card', methods=['POST'])
def add_card():
    if 'user_id' not in session:
        return jsonify({'message': 'User not logged in'}), 401

    user_id = session['user_id']
    card_number = request.json.get('card_number')
    card_holder = request.json.get('card_holder')
    expiry_date = request.json.get('expiry_date')
    cvv = request.json.get('cvv')

    if not (card_number and card_holder and expiry_date and cvv):
        return jsonify({'message': 'All fields are required'}), 400

    # Save payment card information
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO payment_cards (user_id, card_number, card_holder, expiry_date, cvv) VALUES (?, ?, ?, ?, ?)',
        (user_id, card_number, card_holder, expiry_date, cvv)
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'Card added successfully'}), 201

# Route to simulate user registration for testing
@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')

    if not (username and password):
        return jsonify({'message': 'Username and password are required'}), 400

    hashed_password = generate_password_hash(password)
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO users (username, password) VALUES (?, ?)',
        (username, hashed_password)
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'User registered successfully'}), 201

if __name__ == '__main__':
    app.run(debug=True)