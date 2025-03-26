import os
import sqlite3
import secrets
import time
from flask import Flask, request, make_response, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Set a secret key for signing cookies (and other Flask security features)
app.config['SECRET_KEY'] = secrets.token_hex(16)
DATABASE = 'app.db'
SESSION_DURATION = 3600  # Session lifetime in seconds (1 hour)

def get_db():
    """Return a database connection, stored in the Flask global context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with required tables and a test user."""
    db = get_db()
    cur = db.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS sessions")
    
    # Create a users table if it does not exist
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE NOT NULL,
                   password_hash TEXT NOT NULL)''')
    # Create a sessions table to manage login sessions
    cur.execute('''CREATE TABLE IF NOT EXISTS sessions (
                   token TEXT PRIMARY KEY,
                   user_id INTEGER,
                   created_at INTEGER,
                   FOREIGN KEY(user_id) REFERENCES users(id))''')
    # Insert a test user if it does not already exist
    cur.execute("SELECT * FROM users WHERE username = ?", ('testuser',))
    if cur.fetchone() is None:
        hashed = generate_password_hash("test123")
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ('testuser', hashed))
    db.commit()

@app.before_first_request
def initialize():
    """Run initialization routines before handling the first request."""
    init_db()

def create_session(user_id):
    """Generate a secure token, store it in the sessions table and return it."""
    token = secrets.token_urlsafe(32)
    created_at = int(time.time())
    db = get_db()
    db.execute("INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
               (token, user_id, created_at))
    db.commit()
    return token

def get_session(token):
    """Retrieve a session from the database and validate its expiration."""
    db = get_db()
    cur = db.execute("SELECT * FROM sessions WHERE token = ?", (token,))
    session = cur.fetchone()
    if session:
        # Check if the session has expired
        if int(time.time()) - session['created_at'] > SESSION_DURATION:
            db.execute("DELETE FROM sessions WHERE token = ?", (token,))
            db.commit()
            return None
        return session
    return None

def delete_session(token):
    """Remove a session token from the database."""
    db = get_db()
    db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    db.commit()

@app.route('/login', methods=['POST'])
def login():
    """
    Login endpoint:
    - Expects JSON payload with 'username' and 'password'.
    - On successful authentication, creates a session and sets a cookie.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    if user and check_password_hash(user['password_hash'], password):
        token = create_session(user['id'])
        resp = make_response(jsonify({"message": "Logged in"}))
        # The cookie is set with HttpOnly and SameSite=Strict.
        # Not specifying the Domain means the cookie will not be available to subdomains.
        resp.set_cookie("session_token", token, max_age=SESSION_DURATION,
                        httponly=True, samesite='Strict')
        return resp
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/protected')
def protected():
    """
    A protected endpoint that:
    - Reads the session token from cookies.
    - Verifies the session is valid.
    - Returns protected content if authentication passes.
    """
    token = request.cookies.get('session_token')
    if not token:
        return jsonify({"error": "No session token provided"}), 401
    session = get_session(token)
    if not session:
        return jsonify({"error": "Invalid or expired session"}), 401
    db = get_db()
    cur = db.execute("SELECT username FROM users WHERE id = ?", (session['user_id'],))
    user = cur.fetchone()
    return jsonify({"message": f"Hello, {user['username']}! This is protected content."})

@app.route('/logout', methods=['POST'])
def logout():
    """
    Logout endpoint:
    - Deletes the session associated with the cookie.
    - Clears the session cookie.
    """
    token = request.cookies.get('session_token')
    if token:
        delete_session(token)
    resp = make_response(jsonify({"message": "Logged out"}))
    resp.set_cookie("session_token", '', expires=0)
    return resp

@app.route('/test')
def run_tests():
    """
    Testing endpoint:
    Uses Flask’s test client to simulate:
    - A login attempt with invalid credentials.
    - A login attempt with valid credentials.
    - Access to the protected route with a valid session.
    - A logout process.
    Returns a JSON report of the test outcomes.
    """
    with app.test_client() as client:
        # Test login with invalid credentials
        res = client.post('/login', json={'username': 'testuser', 'password': 'wrongpass'})
        invalid_login = res.get_json()

        # Test login with valid credentials
        res = client.post('/login', json={'username': 'testuser', 'password': 'test123'})
        valid_login = res.get_json()
        # Extract the session token from the Set-Cookie header
        token_header = res.headers.get('Set-Cookie')
        token = None
        if token_header:
            # Assuming the cookie is formatted as "session_token=<token>; ..."
            token = token_header.split(';')[0].split('=')[1]

        # Test accessing the protected route with a valid token
        client.set_cookie('localhost', 'session_token', token)
        res = client.get('/protected')
        protected_response = res.get_json()

        # Test logout
        res = client.post('/logout')
        logout_response = res.get_json()

    return jsonify({
        "invalid_login": invalid_login,
        "valid_login": valid_login,
        "protected_response": protected_response,
        "logout_response": logout_response
    })

if __name__ == '__main__':
    # For local testing, run the Flask development server.
    # In production, ensure that HTTPS is used so that Secure cookies can be enforced.
    app.run(debug=True)
