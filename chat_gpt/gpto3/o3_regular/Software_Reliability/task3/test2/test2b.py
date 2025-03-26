from flask import Flask, request, jsonify, g
import sqlite3
import os

# Configuration
DATABASE = 'payment_cards.db'
app = Flask(__name__)
app.config['DEBUG'] = True

def get_db():
    """
    Opens a new database connection if there is none yet for the current application context.
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    """
    Initializes the database by creating the payment_cards table if it doesn't already exist.
    """
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS payment_cards")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_number TEXT NOT NULL,
                expiration_date TEXT NOT NULL,
                cvv TEXT NOT NULL,
                cardholder_name TEXT NOT NULL
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """
    Closes the database again at the end of the request.
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/add_card', methods=['POST'])
def add_card():
    """
    Endpoint to add a new payment card.
    Assumes the user is logged in (using user_id=1 for this example).
    Expects a JSON payload with:
      - card_number (string)
      - expiration_date (string, e.g., "12/26")
      - cvv (string)
      - cardholder_name (string)
    """
    # Simulate logged in user
    user_id = 1

    data = request.get_json()
    required_fields = ['card_number', 'expiration_date', 'cvv', 'cardholder_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    card_number = data['card_number']
    expiration_date = data['expiration_date']
    cvv = data['cvv']
    cardholder_name = data['cardholder_name']

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO payment_cards (user_id, card_number, expiration_date, cvv, cardholder_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, card_number, expiration_date, cvv, cardholder_name))
    db.commit()
    return jsonify({'message': 'Card added successfully'}), 201

@app.route('/test', methods=['GET'])
def test():
    """
    Test endpoint to check if adding a card works.
    It retrieves and returns all payment cards associated with the simulated user (user_id = 1).
    """
    user_id = 1
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, card_number, expiration_date, cvv, cardholder_name FROM payment_cards WHERE user_id = ?', (user_id,))
    cards = cursor.fetchall()
    # Convert the result to a list of dictionaries for better readability
    card_list = [{
        'id': card[0],
        'card_number': card[1],
        'expiration_date': card[2],
        'cvv': card[3],
        'cardholder_name': card[4]
    } for card in cards]
    return jsonify({'cards': card_list})

if __name__ == '__main__':
    # Initialize the database and create tables if necessary.
    init_db()
    app.run()
