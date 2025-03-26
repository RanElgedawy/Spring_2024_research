from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Create database and table if they don't exist
def create_database():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS payment_cards")

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 email TEXT UNIQUE NOT NULL
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS payment_cards (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 card_number TEXT NOT NULL,
                 card_holder_name TEXT NOT NULL,
                 expiration_date TEXT NOT NULL,
                 cvv TEXT NOT NULL,
                 FOREIGN KEY (user_id) REFERENCES users(id)
                 )''')
    conn.commit()
    conn.close()

# Add new payment card
@app.route('/add_card', methods=['POST'])
def add_card():
    user_id = 1  # Replace with actual user ID
    card_number = request.form['card_number']
    card_holder_name = request.form['card_holder_name']
    expiration_date = request.form['expiration_date']
    cvv = request.form['cvv']

    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("INSERT INTO payment_cards (user_id, card_number, card_holder_name, expiration_date, cvv) VALUES (?, ?, ?, ?, ?)", (user_id, card_number, card_holder_name, expiration_date, cvv))
    conn.commit()
    conn.close()

    return redirect(url_for('account'))  # Redirect to account page after adding card

# Account page (for testing)
@app.route('/account')
def account():
    user_id = 1  # Replace with actual user ID
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("SELECT * FROM payment_cards WHERE user_id = ?", (user_id,))
    cards = c.fetchall()
    conn.close()
    return render_template('account.html', cards=cards)

# HTML template for account page (account.html)