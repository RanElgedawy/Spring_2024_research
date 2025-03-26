from flask import Flask, request, session, redirect, url_for, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key in production

DATABASE = 'payment_cards.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS payment_cards")

    # Create users table (for simulation of registered users)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
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
            cardholder_name TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Create a test user for demonstration
def create_test_user():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('testuser', 'password'))
    except sqlite3.IntegrityError:
        # user already exists
        pass
    conn.commit()
    conn.close()

create_test_user()

# Simulated login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('add_card'))
        else:
            return "Invalid credentials", 401
    return '''
        <h2>Login</h2>
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

# Route to add a payment card
@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        cvv = request.form.get('cvv')
        cardholder_name = request.form.get('cardholder_name')
        user_id = session['user_id']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payment_cards (user_id, card_number, expiry_date, cvv, cardholder_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, card_number, expiry_date, cvv, cardholder_name))
        conn.commit()
        conn.close()
        return "Card added successfully!"
    return '''
        <h2>Add Payment Card</h2>
        <form method="post">
            Card Number: <input type="text" name="card_number"><br>
            Expiry Date (MM/YY): <input type="text" name="expiry_date"><br>
            CVV: <input type="text" name="cvv"><br>
            Cardholder Name: <input type="text" name="cardholder_name"><br>
            <input type="submit" value="Add Card">
        </form>
    '''

# Route to list payment cards for the logged in user
@app.route('/cards', methods=['GET'])
def list_cards():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT card_number, expiry_date, cvv, cardholder_name FROM payment_cards WHERE user_id=?", (user_id,))
    cards = cursor.fetchall()
    conn.close()
    return jsonify(cards)

# Function to test if adding a card works using Flask's test client
def run_tests():
    with app.test_client() as client:
        # Simulate logging in with test credentials
        response = client.post('/login', data={'username': 'testuser', 'password': 'password'}, follow_redirects=True)
        if b'Add Payment Card' not in response.data:
            print("Login failed. Test aborted.")
            return

        # Add a payment card
        response = client.post('/add_card', data={
            'card_number': '4111111111111111',
            'expiry_date': '12/25',
            'cvv': '123',
            'cardholder_name': 'John Doe'
        }, follow_redirects=True)
        if b'Card added successfully!' in response.data:
            print("Card addition successful!")
        else:
            print("Card addition failed.")

        # Fetch and display the added cards
        response = client.get('/cards')
        print("Cards for the user:", response.get_json())

if __name__ == '__main__':
    # Uncomment the following line to run tests from the command line.
    # run_tests()
    app.run(debug=True)
