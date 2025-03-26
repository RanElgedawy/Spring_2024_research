from flask import Flask, request, redirect, url_for, session, g
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import timedelta

DATABASE = 'user_sessions.db'
SECRET_KEY = secrets.token_hex(24)  # Generate a strong secret key
SESSION_LIFETIME = timedelta(minutes=30)  # Set the session lifetime (e.g., 30 minutes)
SESSION_COOKIE_NAME = 'session_token'  # Name of the session cookie

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# --- Database Initialization ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
    return db

def close_db():
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

@app.teardown_appcontext
def teardown_db(error):
    close_db()

# --- User Authentication (Assuming Existing User Database) ---
def get_user_by_username(username):
    db = get_db()
    cur = db.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
    return cur.fetchone()

def verify_password(user, password):
    return user and check_password_hash(user['password'], password)

# --- Session Management ---
def create_session(user_id):
    session_token = secrets.token_hex(32)  # Generate a strong session token
    db = get_db()
    # Invalidate any existing sessions for this user
    db.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
    # Create a new session record
    db.execute('INSERT INTO sessions (session_token, user_id) VALUES (?, ?)', (session_token, user_id))
    db.commit()
    # Set the session cookie
    response = redirect(url_for('index'))
    response.set_cookie(SESSION_COOKIE_NAME, session_token,
                        httponly=True, secure=True,
                        domain='localhost',  # Replace with your actual domain
                        max_age=int(SESSION_LIFETIME.total_seconds()))
    return response

def get_current_user():
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        return None
    db = get_db()
    cur = db.execute('SELECT u.id, u.username FROM users u JOIN sessions s ON u.id = s.user_id WHERE s.session_token = ?', (session_token,))
    return cur.fetchone()

def clear_session():
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        db = get_db()
        db.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
        db.commit()
    response = redirect(url_for('index'))
    response.delete_cookie(SESSION_COOKIE_NAME, domain='yourdomain.com') # Ensure correct domain
    return response

# --- Routes ---
@app.route('/')
def index():
    user = get_current_user()
    if user:
        return f"Logged in as {user['username']}. <a href='{url_for('logout')}'>Logout</a>"
    return f"<a href='{url_for('login')}'>Login</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and verify_password(user, password):
            return create_session(user['id'])
        else:
            return "Login failed. Invalid username or password."
    return """
        <form method="post">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required><br><br>
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required><br><br>
            <input type="submit" value="Login">
        </form>
    """

@app.route('/logout')
def logout():
    return clear_session()

@app.route('/protected')
def protected():
    user = get_current_user()
    if not user:
        return "You need to be logged in to access this page. <a href='/login'>Login</a>"
    return f"This is a protected page for user {user['username']}."

if __name__ == '__main__':
    # Create the database and tables if they don't exist
    if not os.path.exists(DATABASE):
        init_db()
        # Create a dummy user for testing
        with app.app_context():
            db = get_db()
            hashed_password = generate_password_hash('testpassword')
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('testuser', hashed_password))
            db.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            db.commit()
            print("Created a dummy user 'testuser' and the 'sessions' table for testing.")

    # Set the domain for the cookie (replace with your actual domain)
    app.config['SESSION_COOKIE_DOMAIN'] = 'localhost'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
    app.run(debug=True, host='0.0.0.0', port=5000) # Consider running on a specific host and port