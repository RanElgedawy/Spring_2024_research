from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Function to initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Create users table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS payment_cards")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE
    )
    ''')
    # Create payment_cards table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payment_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        card_number TEXT NOT NULL,
        expiry_date TEXT NOT NULL,
        cvv TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Function to add a payment card
@app.route('/add_card', methods=['POST'])
def add_card():
    data = request.json
    username = data.get('username')
    card_number = data.get('card_number')
    expiry_date = data.get('expiry_date')
    cvv = data.get('cvv')

    if not (username and card_number and expiry_date and cvv):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Fetch the user ID based on the username
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        user_id = user[0]

        # Insert the payment card into the payment_cards table
        cursor.execute('''
        INSERT INTO payment_cards (user_id, card_number, expiry_date, cvv)
        VALUES (?, ?, ?, ?)
        ''', (user_id, card_number, expiry_date, cvv))

        conn.commit()
        conn.close()
        return jsonify({'message': 'Payment card added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def add_test_user(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
    conn.commit()
    conn.close()

# Add a test user
add_test_user('testuser')

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)