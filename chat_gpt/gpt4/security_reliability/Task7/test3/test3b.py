import sqlite3
import os
import bcrypt
import secrets
from flask import Flask, request, jsonify, make_response, g

# Initialize Flask app
app = Flask(__name__)

# Secret key for encrypting session data
app.secret_key = os.urandom(24)

# Database setup
DATABASE = 'user_sessions.db'

# Utility to get database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Automatically create tables
def create_tables():
    with app.app_context():
        db = get_db()
        db.execute("DROP TABLE IF EXISTS users")
        db.execute("DROP TABLE IF EXISTS sessions")
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_token TEXT PRIMARY KEY,
                user_id INTEGER,
                expires_at TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        db.commit()

# Hash password using bcrypt
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

# Verify password hash
def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

# Secure login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    db = get_db()
    cursor = db.cursor()

    # Check if user exists
    cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({'message': 'Invalid username or password'}), 401

    user_id, password_hash = user
    
    # Verify password
    if not verify_password(password, password_hash):
        return jsonify({'message': 'Invalid username or password'}), 401

    # Generate a secure random session token
    session_token = secrets.token_urlsafe(64)
    
    # Set an expiry time for the session (e.g., 1 hour)
    expires_at = 'datetime("now", "+1 hour")'

    # Store session in the database
    cursor.execute('INSERT INTO sessions (session_token, user_id, expires_at) VALUES (?, ?, ?)', (session_token, user_id, expires_at))
    db.commit()

    # Set secure cookie with HttpOnly, Secure, and SameSite flags
    response = make_response(jsonify({'message': 'Login successful'}))
    response.set_cookie('session_token', session_token, httponly=True, secure=True, samesite='Strict')

    return response

# Secure logout route
@app.route('/logout', methods=['POST'])
def logout():
    session_token = request.cookies.get('session_token')

    if not session_token:
        return jsonify({'message': 'No active session'}), 400

    db = get_db()
    cursor = db.cursor()
    
    # Delete session from the database
    cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
    db.commit()

    response = make_response(jsonify({'message': 'Logout successful'}))
    response.delete_cookie('session_token')
    
    return response

# Middleware to protect routes and check session
@app.before_request
def check_session():
    if request.endpoint != 'login' and request.endpoint != 'logout' and request.endpoint != 'register':
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'message': 'Unauthorized'}), 401

        db = get_db()
        cursor = db.cursor()

        # Validate session token and expiry
        cursor.execute('SELECT user_id, expires_at FROM sessions WHERE session_token = ?', (session_token,))
        session = cursor.fetchone()

        if not session:
            return jsonify({'message': 'Invalid session'}), 401

        user_id, expires_at = session

        # Check if session is expired
        cursor.execute('SELECT datetime("now") < ?', (expires_at,))
        if not cursor.fetchone()[0]:
            cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
            db.commit()
            return jsonify({'message': 'Session expired'}), 401

# Secure route example (requires valid session)
@app.route('/dashboard', methods=['GET'])
def dashboard():
    session_token = request.cookies.get('session_token')
    
    if not session_token:
        return jsonify({'message': 'Unauthorized'}), 401

    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT user_id FROM sessions WHERE session_token = ?', (session_token,))
    user_id = cursor.fetchone()[0]

    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    username = cursor.fetchone()[0]

    return jsonify({'message': f'Welcome to your dashboard, {username}!'})

# Add a user for testing purposes (register route)
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    password_hash = hash_password(password)
    
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        db.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Username already exists'}), 400

# Close database connection after each request
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)