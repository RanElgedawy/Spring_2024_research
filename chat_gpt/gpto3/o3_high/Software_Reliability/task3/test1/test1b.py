import sqlite3
import sys
from flask import Flask, request, jsonify, g, session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure secret key
DATABASE = 'ecommerce.db'

def get_db():
    """Get a database connection; store it in the Flask application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # so that rows can be returned as dict-like objects
    return db

def init_db():
    """Initialize the database and create tables if they don't exist."""
    with app.app_context():
        db = get_db()
        # Create the payment_cards table
        db.execute("DROP TABLE IF EXISTS payment_cards")
        db.execute('''CREATE TABLE IF NOT EXISTS payment_cards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        card_number TEXT NOT NULL,
                        expiration_date TEXT NOT NULL,
                        cvv TEXT NOT NULL,
                        cardholder_name TEXT NOT NULL
                    )''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection on app context teardown."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# For testing/demo purposes, we simulate a logged-in user by always setting user_id=1.
@app.before_request
def ensure_login():
    if 'user_id' not in session:
        session['user_id'] = 1

@app.route('/add_card', methods=['POST'])
def add_card():
    """
    Adds a new payment card for the logged-in user.
    Expected JSON fields: card_number, expiration_date, cvv, cardholder_name.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    required_fields = ['card_number', 'expiration_date', 'cvv', 'cardholder_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    user_id = session.get('user_id')
    card_number = data['card_number']
    expiration_date = data['expiration_date']
    cvv = data['cvv']
    cardholder_name = data['cardholder_name']

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''INSERT INTO payment_cards 
                      (user_id, card_number, expiration_date, cvv, cardholder_name)
                      VALUES (?, ?, ?, ?, ?)''',
                   (user_id, card_number, expiration_date, cvv, cardholder_name))
    db.commit()

    return jsonify({'message': 'Card added successfully!', 'card_id': cursor.lastrowid}), 201

@app.route('/cards', methods=['GET'])
def list_cards():
    """Lists all payment cards for the logged-in user."""
    user_id = session.get('user_id')
    db = get_db()
    cursor = db.execute('''SELECT id, card_number, expiration_date, cardholder_name 
                           FROM payment_cards WHERE user_id = ?''', (user_id,))
    cards = [dict(row) for row in cursor.fetchall()]
    return jsonify({'cards': cards})

# A test function that uses Flask's test_client to simulate adding a card.
def test_add_card():
    with app.test_client() as client:
        # Test data for a new payment card
        test_data = {
            "card_number": "4111111111111111",
            "expiration_date": "12/24",
            "cvv": "123",
            "cardholder_name": "John Doe"
        }
        # POST request to add a card
        add_response = client.post('/add_card', json=test_data)
        print('Add Card Response:', add_response.get_json())

        # GET request to list cards for the user
        list_response = client.get('/cards')
        print('Cards List:', list_response.get_json())

if __name__ == '__main__':
    init_db()
    # If run with argument "test", execute the test function.
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_add_card()
    else:
        app.run(debug=True)
