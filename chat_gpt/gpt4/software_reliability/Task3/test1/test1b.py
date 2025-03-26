from flask import Flask, request, render_template, redirect, url_for
import sqlite3

app = Flask(__name__)

DATABASE = 'ecommerce.db'

def init_db():
    """Initialize the database and create tables if they don't exist."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Create users table (assuming users are already registered)
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS payment_cards")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        ''')
        # Create payment_cards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_number TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                cardholder_name TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()

@app.before_first_request
def setup():
    """Setup the database before handling the first request."""
    init_db()

@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    """Route to add a new payment card."""
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        cardholder_name = request.form.get('cardholder_name')
        
        # Validate input (simple validation for demonstration)
        if not (username and card_number and expiry_date and cardholder_name):
            return "All fields are required.", 400

        # Add payment card to the database
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # Find user by username
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if not user:
                return "User not found.", 404

            # Insert the payment card
            cursor.execute('''
                INSERT INTO payment_cards (user_id, card_number, expiry_date, cardholder_name)
                VALUES (?, ?, ?, ?)
            ''', (user[0], card_number, expiry_date, cardholder_name))
            conn.commit()

        return redirect(url_for('add_card'))

    # Render the form for adding a new card
    return '''
        <form method="POST">
            Username: <input type="text" name="username"><br>
            Card Number: <input type="text" name="card_number"><br>
            Expiry Date (MM/YY): <input type="text" name="expiry_date"><br>
            Cardholder Name: <input type="text" name="cardholder_name"><br>
            <input type="submit" value="Add Card">
        </form>
    '''

if __name__ == '__main__':
    app.run(debug=True)