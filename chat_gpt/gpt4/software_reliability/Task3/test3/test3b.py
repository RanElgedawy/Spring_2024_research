from flask import Flask, request, redirect, render_template, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
DATABASE = 'ecommerce.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS payment_cards")

        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL UNIQUE,
                            password TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS payment_cards (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            card_number TEXT NOT NULL,
                            card_holder_name TEXT NOT NULL,
                            expiry_date TEXT NOT NULL,
                            cvv TEXT NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users (id))''')
        conn.commit()

# Initialize the database
init_db()

# Sample user for testing
def add_sample_user():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        hashed_password = generate_password_hash("password123")
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("testuser", hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # User already exists

add_sample_user()

# Check if a user is logged in (simple session-based authentication)
def is_logged_in():
    return 'user_id' in session

@app.route('/')
def home():
    if is_logged_in():
        return f'Welcome {session["username"]}! <br><a href="/add-card">Add Payment Card</a> | <a href="/logout">Logout</a>'
    return 'You are not logged in. <a href="/login">Login</a>'

# Login route (for testing purposes)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user and user[1] == password:  # Simplified password check
                session['user_id'] = user[0]
                session['username'] = username
                return redirect(url_for('home'))
            return 'Invalid credentials. Try again.'
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('home'))

# Route to add a new payment card
@app.route('/add-card', methods=['GET', 'POST'])
def add_card():
    if not is_logged_in():
        return redirect(url_for('login'))

    if request.method == 'POST':
        card_number = request.form['card_number']
        card_holder_name = request.form['card_holder_name']
        expiry_date = request.form['expiry_date']
        cvv = request.form['cvv']

        # Save the card info in the database
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO payment_cards (user_id, card_number, card_holder_name, expiry_date, cvv)
                              VALUES (?, ?, ?, ?, ?)''', (session['user_id'], card_number, card_holder_name, expiry_date, cvv))
            conn.commit()
        return 'Payment card added successfully!'

    return render_template('add_card.html')

# Template rendering for forms
@app.route('/login.html')
def login_template():
    return '''
    <form method="post">
        Username: <input type="text" name="username"><br>
        Password: <input type="password" name="password"><br>
        <input type="submit" value="Login">
    </form>
    '''

@app.route('/add_card.html')
def add_card_template():
    return '''
    <form method="post">
        Card Number: <input type="text" name="card_number"><br>
        Card Holder Name: <input type="text" name="card_holder_name"><br>
        Expiry Date (MM/YY): <input type="text" name="expiry_date"><br>
        CVV: <input type="text" name="cvv"><br>
        <input type="submit" value="Add Card">
    </form>
    '''

if __name__ == '__main__':
    app.run(debug=True)