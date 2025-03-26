from flask import Flask, request, redirect, url_for, render_template_string, make_response, g
import sqlite3
import os
import uuid
import hashlib
from datetime import datetime, timedelta

DATABASE = './users.db'
app = Flask(__name__)

# --- Database Helpers ---

def get_db():
    """Get a connection to the SQLite database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    """Initialize the database with users and sessions tables."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create users table
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS sessions")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        db.commit()
        
        # Insert a test user if it doesn't exist
        cursor.execute("SELECT * FROM users WHERE username = ?", ('testuser',))
        if not cursor.fetchone():
            # Store a hashed password (using SHA256 for this example)
            password_hash = hashlib.sha256("password".encode()).hexdigest()
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ('testuser', password_hash))
            db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection on app teardown."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Session Helpers ---

def generate_session(user_id):
    """Generate a new session token for a user and store it with expiration."""
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)  # Session expires in 1 hour
    db = get_db()
    db.execute("INSERT INTO sessions (session_id, user_id, expires_at) VALUES (?, ?, ?)",
               (session_id, user_id, expires_at))
    db.commit()
    return session_id

def get_user_by_session(session_id):
    """Validate a session token and return the corresponding username if valid."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id, expires_at FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    if row:
        user_id, expires_at_str = row
        expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d %H:%M:%S.%f')
        if expires_at > datetime.utcnow():
            # Session is valid; retrieve username
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            if user_row:
                return user_row[0]
    return None

# --- Routes ---

@app.route('/')
def index():
    """Protected index page; greets the user if a valid session exists."""
    session_id = request.cookies.get('session')
    if session_id:
        username = get_user_by_session(session_id)
        if username:
            return f"Hello, {username}! You are logged in."
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page: shows a form and sets a session cookie upon successful login."""
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, password_hash))
        row = cursor.fetchone()
        if row:
            user_id = row[0]
            session_id = generate_session(user_id)
            response = make_response(redirect(url_for('index')))
            # Set cookie without specifying domain ensures it is limited to the current host
            response.set_cookie('session', session_id, httponly=True, samesite='Lax')
            return response
        else:
            error = 'Invalid credentials. Please try again.'
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
            <label>Username:</label>
            <input type="text" name="username"><br>
            <label>Password:</label>
            <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
        <p style="color: red;">{{ error }}</p>
        <p>Test user: <strong>testuser</strong> / Password: <strong>password</strong></p>
    ''', error=error)

@app.route('/logout')
def logout():
    """Logs the user out by deleting the session and clearing the cookie."""
    session_id = request.cookies.get('session')
    if session_id:
        db = get_db()
        db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        db.commit()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)
    return response

# --- Run the App ---

if __name__ == '__main__':
    init_db()
    # Running in debug mode for testing; remove debug=True in production.
    app.run(debug=True)
