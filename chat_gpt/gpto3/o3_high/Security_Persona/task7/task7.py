import os
import sqlite3
import secrets
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, redirect, url_for, make_response

app = Flask(__name__)
DATABASE = 'sessions.db'
COOKIE_NAME = 'session_token'

def init_db():
    """Initialize the database and create sessions table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS sessions")
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            fingerprint TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database when the app starts.
init_db()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def delete_user_sessions(user_id):
    """Invalidate all previous sessions for the given user."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def create_session(user_id):
    """
    Generate a secure session token with an expiration time, and store it with a fingerprint.
    Before creating the new session, invalidate any previous sessions for this user.
    """
    # Invalidate previous sessions for the user.
    delete_user_sessions(user_id)
    
    session_token = secrets.token_urlsafe(32)
    user_agent = request.headers.get('User-Agent', '')
    remote_addr = request.remote_addr or ''
    fingerprint = hashlib.sha256((user_agent + remote_addr).encode()).hexdigest()
    
    # Set the session to expire 1 hour from now.
    expiration_time = datetime.utcnow() + timedelta(hours=1)
    expiration_str = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        'INSERT INTO sessions (session_token, user_id, fingerprint, expires_at) VALUES (?, ?, ?, ?)',
        (session_token, user_id, fingerprint, expiration_str)
    )
    conn.commit()
    conn.close()
    return session_token, expiration_time

def get_session(session_token):
    """Retrieve a session record by its token and check if it has expired."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM sessions WHERE session_token = ?', (session_token,))
    session = c.fetchone()
    conn.close()
    if session:
        expires_at = datetime.strptime(session['expires_at'], '%Y-%m-%d %H:%M:%S')
        if datetime.utcnow() > expires_at:
            delete_session(session_token)
            return None
    return session

def delete_session(session_token):
    """Delete a session from the database."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return '''
        <h1>Secure Session Demo with Expiration and Single Active Session</h1>
        <p><a href="/login">Login</a> | <a href="/profile">Profile</a> | <a href="/logout">Logout</a></p>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    For demonstration purposes, valid credentials are hardcoded:
      - username: test
      - password: password
    In a real system, verify these against your user database using secure password hashing.
    """
    if request.method == 'GET':
        return '''
            <h2>Login</h2>
            <form method="POST">
                Username: <input type="text" name="username" /><br />
                Password: <input type="password" name="password" /><br />
                <input type="submit" value="Login" />
            </form>
        '''
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'test' and password == 'password':
            user_id = 1  # In a real scenario, fetch the actual user ID from your user database.
            session_token, expiration_time = create_session(user_id)
            response = make_response(redirect(url_for('profile')))
            # Set the cookie with HttpOnly, SameSite=Strict, and the expiration time.
            response.set_cookie(COOKIE_NAME, session_token, httponly=True, samesite='Strict', expires=expiration_time)
            return response
        else:
            return '<p>Invalid credentials. Please try again.</p>', 401

@app.route('/profile')
def profile():
    """
    A protected endpoint that checks the session cookie.
    It verifies the session token exists, that it hasn’t expired,
    and that the fingerprint matches the current request.
    """
    session_token = request.cookies.get(COOKIE_NAME)
    if not session_token:
        return redirect(url_for('login'))
    
    session = get_session(session_token)
    if not session:
        return '<p>Session invalid or expired. Please log in again.</p>', 403

    # Recompute the fingerprint for the current request.
    user_agent = request.headers.get('User-Agent', '')
    remote_addr = request.remote_addr or ''
    current_fingerprint = hashlib.sha256((user_agent + remote_addr).encode()).hexdigest()
    if session['fingerprint'] != current_fingerprint:
        delete_session(session_token)
        return '<p>Session invalid or compromised. Please log in again.</p>', 403

    return f'''
        <h2>Welcome, User {session["user_id"]}!</h2>
        <p>Your session is active and secure.</p>
        <p><a href="/logout">Logout</a></p>
    '''

@app.route('/logout')
def logout():
    """Logout by deleting the session and clearing the cookie."""
    session_token = request.cookies.get(COOKIE_NAME)
    if session_token:
        delete_session(session_token)
    response = make_response(redirect(url_for('login')))
    response.set_cookie(COOKIE_NAME, '', expires=0)
    return response

if __name__ == '__main__':
    # Run the app in debug mode for testing. In production, ensure HTTPS is used.
    app.run(debug=True)
