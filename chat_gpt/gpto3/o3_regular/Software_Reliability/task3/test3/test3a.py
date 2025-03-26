from flask import Flask, request, session, redirect, url_for, render_template_string
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Connect to the database and create necessary tables if they don't exist.
    conn = get_db_connection()
    cur = conn.cursor()
    # Table to store payment cards. For simplicity, only a few fields are used.
    cur.execute("DROP TABLE IF EXISTS payment_cards")
    cur.execute("DROP TABLE IF EXISTS users")

    cur.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number TEXT NOT NULL,
            expiration_date TEXT NOT NULL,
            cvv TEXT NOT NULL
        )
    ''')
    # A simple users table for login simulation.
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Insert a dummy user if not already present (username: testuser, password: testpass).
    cur.execute('SELECT * FROM users WHERE username = ?', ('testuser',))
    if cur.fetchone() is None:
        cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('testuser', 'testpass'))
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    # Redirect to the card form if logged in; otherwise, to login.
    if 'user_id' in session:
        return redirect(url_for('add_card'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = '''
    <h2>Login</h2>
    <form method="POST">
        Username: <input type="text" name="username" /><br/>
        Password: <input type="password" name="password" /><br/>
        <input type="submit" value="Login" />
    </form>
    '''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('add_card'))
        else:
            return login_form + '<p style="color:red;">Invalid credentials. Please try again.</p>'
    return login_form

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form_html = '''
    <h2>Add Payment Card</h2>
    <form method="POST">
        Card Number: <input type="text" name="card_number" /><br/>
        Expiration Date (MM/YY): <input type="text" name="expiration_date" /><br/>
        CVV: <input type="text" name="cvv" /><br/>
        <input type="submit" value="Add Card" />
    </form>
    <p><a href="/logout">Logout</a></p>
    '''
    if request.method == 'POST':
        user_id = session['user_id']
        card_number = request.form['card_number']
        expiration_date = request.form['expiration_date']
        cvv = request.form['cvv']
        # Insert the card data into the database.
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO payment_cards (user_id, card_number, expiration_date, cvv)
            VALUES (?, ?, ?, ?)
        ''', (user_id, card_number, expiration_date, cvv))
        conn.commit()
        conn.close()
        return form_html + '<p style="color:green;">Card added successfully!</p>'
    return form_html

if __name__ == '__main__':
    app.run(debug=True)
