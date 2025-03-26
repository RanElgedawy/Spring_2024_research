from flask import Flask, request, redirect, render_template, url_for, session, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'ecommerce.db'

# Function to connect to the database
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Close the database connection when the application context ends
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize the database and create tables
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS payment_cards")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                card_number TEXT,
                expiry_date TEXT,
                cardholder_name TEXT,
                cvv TEXT,
                billing_zip TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        db.commit()


# Route to register a user (for testing purposes)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        db.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Route to log in (for testing purposes)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            return redirect(url_for('add_card'))
    
    return render_template('login.html')

# Route to add a new payment card
@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    error = None
    if request.method == 'POST':
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        cardholder_name = request.form.get('cardholder_name')
        cvv = request.form.get('cvv')
        billing_zip = request.form.get('billing_zip')

        # Validation checks
        if not card_number or len(card_number) != 16 or not card_number.isdigit():
            error = "Invalid card number. It must be 16 digits."
        elif not expiry_date or not validate_expiry_date(expiry_date):
            error = "Invalid expiry date. It must be in the format MM/YY and not in the past."
        elif not cardholder_name or len(cardholder_name.strip()) == 0:
            error = "Cardholder name is required."
        elif not cvv or len(cvv) not in [3, 4] or not cvv.isdigit():
            error = "Invalid CVV. It must be 3 or 4 digits."
        elif not billing_zip or len(billing_zip) != 5 or not billing_zip.isdigit():
            error = "Invalid billing zip code. It must be 5 digits."

        if error is None:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO payment_cards (user_id, card_number, expiry_date, cardholder_name, cvv, billing_zip) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], card_number, expiry_date, cardholder_name, cvv, billing_zip))
            db.commit()
            return "Card added successfully!"

    return render_template('add_card.html', error=error)

def validate_expiry_date(expiry_date):
    try:
        # Check if expiry date is in the correct format
        exp_month, exp_year = expiry_date.split('/')
        if len(exp_year) == 2:
            exp_year = '20' + exp_year  # Convert YY to YYYY format
        exp_date = datetime(int(exp_year), int(exp_month), 1)
        now = datetime.now()

        # The card should be valid if the expiration date is in the future
        return exp_date > now.replace(day=1)
    except ValueError:
        return False

if __name__ == '__main__':
    init_db()
    app.run(debug=True)