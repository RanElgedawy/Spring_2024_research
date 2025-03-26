from flask import Flask, request, jsonify, render_template_string, g
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'cards.db'

# --- Database Helpers ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Use detect_types for better date/time support if needed
        db = g._database = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cursor = db.cursor()
    # Create payment_cards table if it doesn't exist
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_holder TEXT NOT NULL,
            card_number TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cvv TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Routes ---
# Home page with a form to add a card
@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Add Payment Card</title>
    </head>
    <body>
        <h1>Add Payment Card</h1>
        <form id="cardForm">
            <label for="card_holder">Card Holder:</label><br>
            <input type="text" id="card_holder" name="card_holder" required><br><br>
            
            <label for="card_number">Card Number:</label><br>
            <input type="text" id="card_number" name="card_number" required><br><br>
            
            <label for="expiry_date">Expiry Date (MM/YY):</label><br>
            <input type="text" id="expiry_date" name="expiry_date" required><br><br>
            
            <label for="cvv">CVV:</label><br>
            <input type="text" id="cvv" name="cvv" required><br><br>
            
            <input type="submit" value="Add Card">
        </form>
        <div id="result" style="margin-top:20px;"></div>
        <script>
            document.getElementById('cardForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const data = {
                    card_holder: document.getElementById('card_holder').value,
                    card_number: document.getElementById('card_number').value,
                    expiry_date: document.getElementById('expiry_date').value,
                    cvv: document.getElementById('cvv').value
                };
                fetch('/add_card', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(result => {
                    document.getElementById('result').innerText = JSON.stringify(result);
                })
                .catch(error => {
                    document.getElementById('result').innerText = 'Error: ' + error;
                });
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

# Endpoint to add a new payment card
@app.route('/add_card', methods=['POST'])
def add_card():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # For this demo, assume logged-in user has user_id = 1.
    user_id = 1
    card_holder = data.get('card_holder')
    card_number = data.get('card_number')
    expiry_date = data.get('expiry_date')
    cvv = data.get('cvv')

    if not all([card_holder, card_number, expiry_date, cvv]):
        return jsonify({'error': 'Missing required fields'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO payment_cards (user_id, card_holder, card_number, expiry_date, cvv)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, card_holder, card_number, expiry_date, cvv))
    db.commit()

    return jsonify({'message': 'Card added successfully', 'card_id': cursor.lastrowid})

# Endpoint to list payment cards for the current user (for testing)
@app.route('/list_cards', methods=['GET'])
def list_cards():
    # For this demo, assume logged-in user has user_id = 1.
    user_id = 1
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM payment_cards WHERE user_id = ?', (user_id,))
    cards = cursor.fetchall()
    # Convert rows to dictionaries for JSON serialization
    cards_list = [dict(card) for card in cards]
    return jsonify(cards_list)

if __name__ == '__main__':
    # Initialize the DB and create tables automatically
    if not os.path.exists(DATABASE):
        with app.app_context():
            init_db()
    app.run(debug=True)
