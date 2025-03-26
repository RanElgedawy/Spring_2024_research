from flask import Flask, request, redirect, url_for, make_response
import sqlite3
import secrets
import os
import time  # used to set/check expiration

app = Flask(__name__)
DATABASE = 'test.db'

SESSION_DURATION = 30*60  # 30 minutes in seconds

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS sessions")
    cursor.execute("DROP TABLE IF EXISTS users")

    # Create a users table (if not already exists)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Create a sessions table with an expiration timestamp
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def create_test_user():
    # Insert a test user if it does not exist yet.
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('testuser', 'password'))
    except sqlite3.IntegrityError:
        # Test user already exists
        pass
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return '''
    <h1>Welcome to the E-Commerce Site</h1>
    <p><a href="/login">Login</a></p>
    <p><a href="/dashboard">Dashboard (protected)</a></p>
    <p><a href="/logout">Logout</a></p>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve username and password from form data
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_connection()
        cursor = conn.cursor()
        # For simplicity, password is stored in plain text.
        # In production, always store hashed passwords!
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        if user:
            # Invalidate any previous sessions for this user
            cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user['id'],))
            conn.commit()

            # Generate a secure random session token and set expiration time
            session_token = secrets.token_hex(16)
            expires_at = int(time.time()) + SESSION_DURATION
            cursor.execute('INSERT INTO sessions (session_token, user_id, expires_at) VALUES (?, ?, ?)',
                           (session_token, user['id'], expires_at))
            conn.commit()
            conn.close()
            # Set cookie without a Domain attribute, and add max_age for expiration.
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie('session_token', session_token,
                                httponly=True, samesite='Lax', max_age=SESSION_DURATION)
            return response
        else:
            conn.close()
            return 'Invalid credentials. Please try again.', 401
    # GET request: show the login form
    return '''
    <h1>Login</h1>
    <form method="post">
      <label>Username: <input type="text" name="username"></label><br>
      <label>Password: <input type="password" name="password"></label><br>
      <input type="submit" value="Login">
    </form>
    '''

def get_current_user():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, expires_at FROM sessions WHERE session_token = ?', (session_token,))
    session = cursor.fetchone()
    if session:
        current_time = int(time.time())
        if current_time > session['expires_at']:
            # Session expired, remove it
            cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
            conn.commit()
            conn.close()
            return None
        # If session is valid, fetch the user details.
        cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        return user
    conn.close()
    return None

@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    return f"<h1>Dashboard</h1><p>Welcome, {user['username']}!</p>"

@app.route('/logout')
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
        conn.commit()
        conn.close()
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('session_token')
    return response

if __name__ == '__main__':
    # Initialize the DB and add a test user if the database does not exist.
    if not os.path.exists(DATABASE):
        init_db()
        create_test_user()
    app.run(debug=True)
