from flask import Flask, request, jsonify, session
import sqlite3
from contextlib import closing

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with a strong key in production

DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Create tables if they do not exist.
    conn = get_db()
    cursor = conn.cursor()
    # Dummy users table (assume users are pre-registered)
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL
        );
    ''')
    # Table to store payment card information.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            card_number TEXT NOT NULL,
            cardholder_name TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cvv TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    ''')
    conn.commit()
    conn.close()

@app.before_first_request
def initialize():
    init_db()
    # For testing, create a dummy user with id=1 if not exists.
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?,?)", (1, 'testuser'))
    conn.commit()
    conn.close()

# Simulate a logged-in user (in production, use a real authentication system)
@app.before_request
def fake_login():
    session['user_id'] = 1

@app.route('/add_card', methods=['POST'])
def add_card():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.get_json()
    required_fields = ['card_number', 'cardholder_name', 'expiry_date', 'cvv']
    if not data or any(field not in data for field in required_fields):
        return jsonify({'error': 'Missing required card details'}), 400

    user_id = session['user_id']
    card_number = data['card_number']
    cardholder_name = data['cardholder_name']
    expiry_date = data['expiry_date']
    cvv = data['cvv']

    # Insert the card details into the database.
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payment_cards (user_id, card_number, cardholder_name, expiry_date, cvv)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, card_number, cardholder_name, expiry_date, cvv))
    conn.commit()
    card_id = cursor.lastrowid
    conn.close()

    return jsonify({'message': 'Card added successfully', 'card_id': card_id}), 201

# HTML form to test card addition using JavaScript (AJAX)
@app.route('/card_form')
def card_form():
    return '''
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <title>Add Payment Card</title>
      </head>
      <body>
        <h2>Add Payment Card</h2>
        <form id="cardForm">
          <label>Card Number: <input type="text" name="card_number" required /></label><br><br>
          <label>Cardholder Name: <input type="text" name="cardholder_name" required /></label><br><br>
          <label>Expiry Date (MM/YY): <input type="text" name="expiry_date" required /></label><br><br>
          <label>CVV: <input type="text" name="cvv" required /></label><br><br>
          <button type="submit">Add Card</button>
        </form>
        <div id="result" style="margin-top:20px; color: green;"></div>
        <script>
          document.getElementById('cardForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            const response = await fetch('/add_card', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(data)
            });
            const result = await response.json();
            document.getElementById('result').innerText = JSON.stringify(result);
          });
        </script>
      </body>
    </html>
    '''

# A simple route to test adding a card programmatically using Flask's test client.
@app.route('/test_add_card', methods=['GET'])
def test_add_card():
    test_data = {
        'card_number': '4111111111111111',
        'cardholder_name': 'John Doe',
        'expiry_date': '12/24',
        'cvv': '123'
    }
    with app.test_client() as client:
        response = client.post('/add_card', json=test_data)
        return jsonify({
            'status_code': response.status_code,
            'response': response.get_json()
        })

if __name__ == '__main__':
    app.run(debug=True)
