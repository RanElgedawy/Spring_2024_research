from flask import Flask, request, redirect, url_for, render_template, make_response
import sqlite3
import hashlib

app = Flask(__name__)

# Database setup function
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Create users table if it doesn't exist
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    # Create a test user
    cursor.execute('''
    INSERT INTO users (username, password) VALUES (?, ?)
    ''', ('testuser', hashlib.sha256('password'.encode()).hexdigest()))
    conn.commit()
    conn.close()

# Function to validate user login
def validate_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM users WHERE username = ? AND password = ?
    ''', (username, hashlib.sha256(password.encode()).hexdigest()))
    user = cursor.fetchone()
    conn.close()
    return user is not None

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if validate_user(username, password):
            resp = make_response(redirect(url_for('home')))
            resp.set_cookie('session_id', username, httponly=True, samesite='Lax')
            return resp
        else:
            return 'Invalid credentials', 401
    return render_template('login.html')

# Route for home page
@app.route('/home')
def home():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return redirect(url_for('login'))
    return f'Welcome, {session_id}! You are logged in.'

# Route for logout
@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('session_id', '', expires=0)
    return resp

# Main route
@app.route('/')
def index():
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Initialize the database
    init_db()
    # Run the app
    app.run(debug=True)