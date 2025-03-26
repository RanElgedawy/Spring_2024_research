# app.py (Backend)
from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # In production, use proper secret management

# Initialize database
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS payment_cards")
    c.execute("DROP TABLE IF EXISTS users")

    # Create payment_cards table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS payment_cards
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  card_number TEXT NOT NULL,
                  expiry_date TEXT NOT NULL,
                  cvv TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create users table (simplified for demo)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Simulate user login for testing
@app.route('/simulate_login/<username>')
def simulate_login(username):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, 'testpass')", (username,))
    conn.commit()
    conn.close()
    
    session['user_id'] = 1  # Simplified for demo - should get actual user ID from DB
    return f"Logged in as {username}"

@app.route('/add_card', methods=['POST'])
def add_card():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    
    # Basic validation
    required_fields = ['card_number', 'expiry_date', 'cvv']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing fields'}), 400

    # Insert into database
    try:
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        c.execute('''INSERT INTO payment_cards 
                     (user_id, card_number, expiry_date, cvv)
                     VALUES (?, ?, ?, ?)''',
                  (session['user_id'], data['card_number'], 
                   data['expiry_date'], data['cvv']))
        conn.commit()
        return jsonify({'message': 'Card added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/card_form')
def card_form():
    return render_template('card_form2.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)