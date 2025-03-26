from flask import Flask, request, jsonify, make_response
import sqlite3
import uuid
import datetime

app = Flask(__name__)
DATABASE = 'test.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Create the users table.
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS sessions")

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    # Create the sessions table.
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE,
            expires_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Insert a test user if not already present.
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("testuser", "password"))
    except sqlite3.IntegrityError:
        pass  # User already exists.
    conn.commit()
    conn.close()

@app.before_first_request
def setup():
    init_db()

def create_session(user_id):
    """Creates a new session for a user and returns the session token."""
    session_token = str(uuid.uuid4())
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
        (user_id, session_token, expires_at)
    )
    conn.commit()
    conn.close()
    return session_token

def get_user_by_session(token):
    """Validates a session token and returns the user_id if valid."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT user_id, expires_at FROM sessions WHERE session_token = ?", (token,))
    row = c.fetchone()
    conn.close()
    if row:
        user_id, expires_at_str = row
        expires_at = datetime.datetime.strptime(expires_at_str, '%Y-%m-%d %H:%M:%S.%f')
        if datetime.datetime.utcnow() < expires_at:
            return user_id
    return None

@app.route('/login', methods=['POST'])
def login():
    """
    Login endpoint.
    Expects JSON with "username" and "password". If valid, creates a session
    and sets a cookie named "session_token" (HTTP-only, same-site).
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    row = c.fetchone()
    conn.close()

    if row:
        user_id = row[0]
        session_token = create_session(user_id)
        resp = make_response(jsonify({'message': 'Login successful'}))
        # Not specifying the domain attribute restricts the cookie to the current domain only.
        resp.set_cookie('session_token', session_token, httponly=True, samesite='Lax')
        return resp
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/protected')
def protected():
    """
    Protected endpoint.
    Checks for a valid session cookie and returns protected content if the user is authenticated.
    """
    token = request.cookies.get('session_token')
    if token and get_user_by_session(token):
        return jsonify({'message': 'You have access to protected content.'})
    else:
        return jsonify({'message': 'Unauthorized'}), 401

@app.route('/logout')
def logout():
    """
    Logout endpoint.
    Deletes the session from the database and clears the session cookie.
    """
    token = request.cookies.get('session_token')
    if token:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("DELETE FROM sessions WHERE session_token = ?", (token,))
        conn.commit()
        conn.close()
    resp = make_response(jsonify({'message': 'Logged out'}))
    resp.delete_cookie('session_token')
    return resp

if __name__ == '__main__':
    app.run(debug=True)
