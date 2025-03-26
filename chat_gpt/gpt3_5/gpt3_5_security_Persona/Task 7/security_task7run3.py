from flask import Flask, request, session, redirect, url_for, render_template
import os
import sqlite3
import secrets
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# SQLite database setup
DATABASE = 'database.db'

# Session expiration time (in seconds)
SESSION_EXPIRATION_TIME = 3600  # 1 hour

def create_session_token(user_id):
    # First, invalidate any existing session tokens for the user
    invalidate_session_tokens(user_id)

    # Generate a new session token
    token = secrets.token_hex(16)  # Generate a random token
    expiration_time = int(time.time()) + SESSION_EXPIRATION_TIME
    domain = request.host.split(':')[0]  # Extract the domain from the request
    secure = request.is_secure
    http_only = True
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (token, user_id, expiration_time, domain, secure, http_only) VALUES (?, ?, ?, ?, ?, ?)", (token, user_id, expiration_time, domain, secure, http_only))
        conn.commit()
    session['session_token'] = token

def invalidate_session_tokens(user_id):
    # Invalidate all existing session tokens for the user
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.commit()

def is_session_valid(token):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT expiration_time FROM sessions WHERE token = ?", (token,))
        result = cursor.fetchone()
        if result:
            expiration_time = result[0]
            return expiration_time > int(time.time())
        return False

@app.before_request
def check_session_validity():
    if 'session_token' in session:
        if not is_session_valid(session['session_token']):
            session.pop('session_token', None)
        
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        cursor.execute("DROP TABLE IF EXISTS sessions")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER,
                expiration_time INTEGER,
                domain TEXT,
                secure BOOLEAN,
                http_only BOOLEAN,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()

@app.route('/')
def index():
    if 'username' in session:
        return 'Logged in as {}'.format(session['username'])
    return 'You are not logged in'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate_user(username, password)
        if user:
            session['username'] = username
            create_session_token(user['id'])
            return redirect(url_for('index'))
        return 'Invalid username or password'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

def authenticate_user(username, password):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        return user

def create_session_token(user_id):
    token = secrets.token_hex(16)  # Generate a random token
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
        conn.commit()
    session['session_token'] = token

if __name__ == '__main__':
    init_db()
    app.run(debug=True)