from flask import Flask, request, render_template_string, redirect, url_for, flash, session
import sqlite3
from contextlib import closing

app = Flask(__name__)
app.secret_key = 'replace-this-secret-key'  # Change this in production

DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    cursor = db.cursor()
    # Create table for payment cards
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_number TEXT,
            cardholder_name TEXT,
            expiration_date TEXT,
            cvv TEXT
        )
    ''')
    # Create table for users (for demo purposes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE
        )
    ''')
    # Insert a dummy user if it doesn't exist
    cursor.execute('SELECT * FROM users WHERE username = ?', ('testuser',))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (username) VALUES (?)', ('testuser',))
    db.commit()
    db.close()

@app.before_first_request
def initialize():
    init_db()

# Simple route to simulate a login for demo purposes
@app.route('/login')
def login():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", ('testuser',)).fetchone()
    session['user_id'] = user['id']
    flash('Logged in as testuser')
    return redirect(url_for('add_card'))

# Route to add a new payment card
@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        card_number = request.form['card_number']
        cardholder_name = request.form['cardholder_name']
        expiration_date = request.form['expiration_date']
        cvv = request.form['cvv']
        
        db = get_db()
        db.execute('''
            INSERT INTO payment_cards (user_id, card_number, cardholder_name, expiration_date, cvv)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], card_number, cardholder_name, expiration_date, cvv))
        db.commit()
        flash('Card added successfully!')
        return redirect(url_for('add_card'))
    
    return render_template_string('''
        <!doctype html>
        <title>Add Payment Card</title>
        <h1>Add Payment Card</h1>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <ul>
            {% for message in messages %}
              <li>{{ message }}</li>
            {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
        <form method="post">
          <p><input type="text" name="card_number" placeholder="Card Number" required></p>
          <p><input type="text" name="cardholder_name" placeholder="Cardholder Name" required></p>
          <p><input type="text" name="expiration_date" placeholder="Expiration Date (MM/YY)" required></p>
          <p><input type="text" name="cvv" placeholder="CVV" required></p>
          <p><input type="submit" value="Add Card"></p>
        </form>
        <p><a href="{{ url_for('view_cards') }}">View your cards</a></p>
    ''')

# Route to view all payment cards for the logged-in user
@app.route('/cards')
def view_cards():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))
    
    db = get_db()
    cards = db.execute('SELECT * FROM payment_cards WHERE user_id = ?', (session['user_id'],)).fetchall()
    return render_template_string('''
        <!doctype html>
        <title>Your Payment Cards</title>
        <h1>Your Payment Cards</h1>
        <ul>
        {% for card in cards %}
          <li>{{ card.card_number }} - {{ card.cardholder_name }} - {{ card.expiration_date }}</li>
        {% else %}
          <li>No cards added yet.</li>
        {% endfor %}
        </ul>
        <p><a href="{{ url_for('add_card') }}">Add another card</a></p>
    ''', cards=cards)

if __name__ == '__main__':
    app.run(debug=True)
