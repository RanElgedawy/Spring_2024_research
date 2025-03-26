from flask import Flask, request, render_template, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Database setup
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_number TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cvv TEXT NOT NULL,
            name_on_card TEXT NOT NULL,
            billing_zip TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Function to create test users
def create_test_users():
    users = [
        ("john_doe",),
        ("jane_smith",),
        ("alice_wonder",)
    ]
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT OR IGNORE INTO users (username)
        VALUES (?)
    ''', users)
    conn.commit()
    conn.close()

# Function to validate expiration date
def validate_expiry_date(expiry_date):
    try:
        expiry = datetime.strptime(expiry_date, "%m/%y")
        current_date = datetime.now()
        # Ensure the card expiration date is in the future
        return expiry > current_date
    except ValueError:
        return False

# Add card form route
@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if request.method == 'POST':
        username = request.form['username']
        card_number = request.form['card_number']
        expiry_date = request.form['expiry_date']
        cvv = request.form['cvv']
        name_on_card = request.form['name_on_card']
        billing_zip = request.form['billing_zip']

        # Check if all fields are filled
        if not all([username, card_number, expiry_date, cvv, name_on_card, billing_zip]):
            flash('All fields are required!', 'danger')
            return redirect(url_for('add_card'))

        # Validate expiration date
        if not validate_expiry_date(expiry_date):
            flash('Invalid expiration date! The date must be in the format MM/YY and must be in the future.', 'danger')
            return redirect(url_for('add_card'))

        # Check if user exists
        conn = sqlite3.connect('ecommerce.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user:
            user_id = user[0]
            # Save card to database
            cursor.execute('''
                INSERT INTO payment_cards (user_id, card_number, expiry_date, cvv, name_on_card, billing_zip)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, card_number, expiry_date, cvv, name_on_card, billing_zip))
            conn.commit()
            flash('Payment card added successfully!', 'success')
        else:
            flash('User not found!', 'danger')

        conn.close()
        return redirect(url_for('add_card'))

    return render_template('add_card.html')

# Test route to verify card entries
@app.route('/test_cards', methods=['GET'])
def test_cards():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT users.username, payment_cards.card_number, payment_cards.expiry_date,
               payment_cards.name_on_card, payment_cards.billing_zip
        FROM payment_cards
        JOIN users ON payment_cards.user_id = users.id
    ''')
    cards = cursor.fetchall()
    conn.close()
    return render_template('test_cards.html', cards=cards)

if __name__ == '__main__':
    init_db()  # Initialize the database
    create_test_users()  # Add test users
    app.run(debug=True)