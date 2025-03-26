from flask import Flask, request, session, redirect, url_for, render_template_string, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
# Replace this with a secure random key in production
app.secret_key = 'replace_this_with_a_secure_random_value'
DATABASE = 'users.db'

def init_db():
    # Create the database file and table if they don't exist
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    # Use Row to access columns by name
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    if 'username' in session:
        return render_template_string('''
            <h1>Welcome, {{ username }}!</h1>
            <p>You are logged in.</p>
            <a href="{{ url_for('logout') }}">Logout</a>
        ''', username=session['username'])
    return render_template_string('''
        <h1>Home</h1>
        <p><a href="{{ url_for('login') }}">Login</a> or <a href="{{ url_for('register') }}">Register</a></p>
    ''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']
        # Hash the password using a secure algorithm
        hashed_password = generate_password_hash(password)
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another one.')
    return render_template_string('''
        <h1>Register</h1>
        <form method="post">
            <label>Username:</label>
            <input type="text" name="username" required><br>
            <label>Password:</label>
            <input type="password" name="password" required><br>
            <input type="submit" value="Register">
        </form>
        <p>Already registered? <a href="{{ url_for('login') }}">Login here</a></p>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        # Check if the user exists and the provided password matches the stored hashed password
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash('Logged in successfully.')
            return redirect(url_for('home'))
        else:
            flash('Incorrect username or password.')
    return render_template_string('''
        <h1>Login</h1>
        <form method="post">
            <label>Username:</label>
            <input type="text" name="username" required><br>
            <label>Password:</label>
            <input type="password" name="password" required><br>
            <input type="submit" value="Login">
        </form>
        <p>New user? <a href="{{ url_for('register') }}">Register here</a></p>
    ''')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('home'))

if __name__ == '__main__':
    # Run the application in debug mode for testing purposes.
    app.run(debug=True)
