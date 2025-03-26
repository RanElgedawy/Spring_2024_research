from flask import Flask, request, jsonify, g, render_template
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Database setup
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create tables if they don't exist
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS payment_cards")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_number TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                cvv TEXT NOT NULL,
                cardholder_name TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        db.commit()

# Route to add a payment card
@app.route('/add_card', methods=['POST'])
def add_card():
    user_id = request.form.get('user_id')  # In real-world scenario, use authentication to get user ID
    card_number = request.form.get('card_number')
    expiry_date = request.form.get('expiry_date')
    cvv = request.form.get('cvv')
    cardholder_name = request.form.get('cardholder_name')

    if not all([user_id, card_number, expiry_date, cvv, cardholder_name]):
        return jsonify({'error': 'All fields are required'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO payment_cards (user_id, card_number, expiry_date, cvv, cardholder_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, card_number, expiry_date, cvv, cardholder_name))
    db.commit()
    return jsonify({'message': 'Payment card added successfully'}), 201

# Sample route to test adding a card using a simple HTML form
@app.route('/test_add_card')
def test_add_card():
    return render_template('add_card.html')

# Create a simple user for testing
def create_sample_user():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username) VALUES ('test_user')")
        db.commit()

if __name__ == '__main__':
    init_db()
    create_sample_user()
    app.run(debug=True)