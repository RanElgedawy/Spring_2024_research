import sqlite3
from flask import Flask, request, render_template, redirect, url_for, session
from functools import wraps
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong, random key

DATABASE = 'ecommerce.db'

# --- Database Initialization ---
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def close_db(conn):
    if conn:
        conn.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        close_db(db)

# Create the schema.sql file
with open('schema.sql', 'w') as f:
    f.write("""
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

DROP TABLE IF EXISTS payment_cards;
CREATE TABLE payment_cards (
    card_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    cardholder_name TEXT NOT NULL,
    card_number TEXT NOT NULL,
    expiry_month INTEGER NOT NULL,
    expiry_year INTEGER NOT NULL,
    cvv TEXT NOT NULL,
    billing_zip TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);
""")

# Initialize the database (run this once)
# init_db() # Uncomment this line once to update your database schema

# --- Dummy User Authentication (Replace with your actual authentication) ---
@app.before_request
def before_request():
    session['user_id'] = 1

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE user_id = ?", (session.get('user_id'),)).fetchone()
    if not user:
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('testuser', 'password'))
        db.commit()
    close_db(db)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes and Functions ---

@app.route('/add_card', methods=['GET', 'POST'])
@login_required
def add_card():
    if request.method == 'POST':
        cardholder_name = request.form['cardholder_name']
        card_number = request.form['card_number']
        expiry_month = request.form['expiry_month']
        expiry_year = request.form['expiry_year']
        cvv = request.form['cvv']
        billing_zip = request.form['billing_zip']  # Get billing zip code

        if not all([cardholder_name, card_number, expiry_month, expiry_year, cvv, billing_zip]):
            return render_template('add_card.html', error='All fields are required.')

        try:
            expiry_month = int(expiry_month)
            expiry_year = int(expiry_year)
        except ValueError:
            return render_template('add_card.html', error='Invalid expiry month or year.')

        if not (1 <= expiry_month <= 12) or len(str(expiry_year)) != 4 or not cvv.isdigit():
            return render_template('add_card.html', error='Invalid expiry month, year, or CVV format.')

        # Validate expiration date
        now = datetime.datetime.now()
        current_year = now.year
        current_month = now.month

        if expiry_year < current_year:
            return render_template('add_card.html', error='Expiration year cannot be in the past.')
        elif expiry_year == current_year and expiry_month < current_month:
            return render_template('add_card.html', error='Expiration month cannot be in the past for the current year.')

        db = get_db()
        try:
            db.execute(
                "INSERT INTO payment_cards (user_id, cardholder_name, card_number, expiry_month, expiry_year, cvv, billing_zip) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session['user_id'], cardholder_name, card_number, expiry_month, expiry_year, cvv, billing_zip)
            )
            db.commit()
            close_db(db)
            return render_template('add_card_success.html')
        except sqlite3.Error as e:
            close_db(db)
            return render_template('add_card.html', error=f'Database error: {e}')

    return render_template('add_card.html')

@app.route('/cards')
@login_required
def view_cards():
    db = get_db()
    cards = db.execute("SELECT * FROM payment_cards WHERE user_id = ?", (session['user_id'],)).fetchall()
    close_db(db)
    return render_template('view_cards.html', cards=cards)

@app.route('/')
def index():
    return "E-commerce Website"

# --- HTML Templates ---
if __name__ == '__main__':
    app.run(debug=True)