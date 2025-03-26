import os
import sqlite3
import secrets
import datetime
from flask import Flask, request, jsonify, make_response, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['DATABASE'] = os.path.join(app.root_path, 'app.db')
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a strong secret in production

# Session duration set to 1 hour
SESSION_DURATION = datetime.timedelta(hours=1)

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initializes the database with sessions and a dummy users table for testing."""
    db = get_db()
    cursor = db.cursor()
    # Create sessions table to store session tokens
    cursor.execute("DROP TABLE IF EXISTS sessions")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_token TEXT PRIMARY KEY,
            user_id INTEGER,
            expires_at DATETIME
        )
    ''')
    # Create a dummy users table (for testing purposes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    db.commit()
    # Insert a dummy user if not already present (username: test, password: test)
    cursor.execute("SELECT * FROM users WHERE username = ?", ('test',))
    if cursor.fetchone() is None:
        password_hash = generate_password_hash('test')
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('test', password_hash))
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.before_first_request
def setup():
    """Initializes the database before handling the first request."""
    init_db()

def create_session(user_id):
    """Creates a new session token for a given user and stores it in the database."""
    db = get_db()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.datetime.utcnow() + SESSION_DURATION
    db.execute('INSERT INTO sessions (session_token, user_id, expires_at) VALUES (?, ?, ?)',
               (token, user_id, expires_at))
    db.commit()
    return token

def get_session(token):
    """Retrieves a session from the database and validates its expiration."""
    db = get_db()
    cursor = db.execute('SELECT * FROM sessions WHERE session_token = ?', (token,))
    session = cursor.fetchone()
    if session:
        # Parse the stored expiration datetime
        expires_at = datetime.datetime.strptime(session['expires_at'], '%Y-%m-%d %H:%M:%S.%f')
        if expires_at < datetime.datetime.utcnow():
            # Session expired: delete it from the database
            db.execute('DELETE FROM sessions WHERE session_token = ?', (token,))
            db.commit()
            return None
        return session
    return None

@app.route('/login', methods=['POST'])
def login():
    """
    Expects a JSON payload with 'username' and 'password'.
    On successful authentication, creates a session and sets a secure cookie.
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400

    username = data['username']
    password = data['password']
    db = get_db()
    cursor = db.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Create a session token for the authenticated user
    token = create_session(user['id'])
    response = make_response(jsonify({'message': 'Logged in successfully'}))
    
    # Set a secure cookie:
    # - 'HttpOnly' prevents access via JavaScript.
    # - 'Secure' ensures transmission over HTTPS.
    # - 'SameSite=Strict' defends against CSRF.
    # - Not setting the 'Domain' attribute restricts the cookie to this host only.
    response.set_cookie(
        'session_token',
        token,
        max_age=SESSION_DURATION.total_seconds(),
        httponly=True,
        secure=True,
        samesite='Strict'
    )
    return response

@app.route('/logout', methods=['POST'])
def logout():
    """
    Deletes the current session from the database and clears the cookie.
    """
    token = request.cookies.get('session_token')
    if token:
        db = get_db()
        db.execute('DELETE FROM sessions WHERE session_token = ?', (token,))
        db.commit()
    response = make_response(jsonify({'message': 'Logged out successfully'}))
    response.set_cookie('session_token', '', expires=0)
    return response

@app.route('/protected', methods=['GET'])
def protected():
    """
    A protected endpoint that requires a valid session.
    Returns a greeting if the session is valid.
    """
    token = request.cookies.get('session_token')
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401

    session = get_session(token)
    if not session:
        return jsonify({'error': 'Session expired or invalid'}), 401

    return jsonify({'message': f'Hello user {session["user_id"]}, you have access to protected content!'})

if __name__ == '__main__':
    # Running in debug mode for testing; in production, use a proper WSGI server
    app.run(debug=True)
