from flask import Flask, request, make_response, jsonify
import sqlite3
import secrets
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Use a strong random key in production
DB_FILE = 'session.db'

def init_db():
    """Initialize the sessions database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS sessions")
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_token TEXT PRIMARY KEY,
            user_id INTEGER,
            expires_at DATETIME
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def create_session(user_id):
    """Create a new session for a user and store it in the database."""
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO sessions (session_token, user_id, expires_at) VALUES (?, ?, ?)",
              (session_token, user_id, expires_at))
    conn.commit()
    conn.close()
    return session_token

def get_session(session_token):
    """Retrieve session details if valid (i.e. not expired)."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, expires_at FROM sessions WHERE session_token = ?", (session_token,))
    row = c.fetchone()
    conn.close()
    if row:
        user_id, expires_at_str = row
        expires_at = datetime.datetime.strptime(expires_at_str, '%Y-%m-%d %H:%M:%S.%f')
        if expires_at < datetime.datetime.utcnow():
            return None  # Session expired
        return {'user_id': user_id, 'expires_at': expires_at}
    return None

def delete_session(session_token):
    """Delete a session from the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
    conn.commit()
    conn.close()

@app.route('/login', methods=['POST'])
def login():
    """
    Test login endpoint.
    For demonstration purposes, accept JSON payload:
    {
      "username": "test",
      "password": "password"
    }
    In a real scenario, validate against your user database.
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing credentials'}), 400

    username = data['username']
    password = data['password']

    # Dummy authentication: replace with your own user database validation
    if username == 'test' and password == 'password':
        user_id = 1  # dummy user id
        session_token = create_session(user_id)
        response = make_response(jsonify({'message': 'Logged in successfully'}))
        # Setting a secure cookie: no Domain attribute means it won't be shared with subdomains.
        response.set_cookie(
            'session_token',
            session_token,
            httponly=True,
            secure=True,
            samesite='Strict'
        )
        return response
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint to delete the session."""
    session_token = request.cookies.get('session_token')
    if session_token:
        delete_session(session_token)
    response = make_response(jsonify({'message': 'Logged out successfully'}))
    response.delete_cookie('session_token')
    return response

@app.route('/protected')
def protected():
    """Protected endpoint that requires a valid session cookie."""
    session_token = request.cookies.get('session_token')
    if not session_token:
        return jsonify({'error': 'No session token provided'}), 401

    session_data = get_session(session_token)
    if not session_data:
        return jsonify({'error': 'Invalid or expired session'}), 401

    return jsonify({
        'message': 'Access granted to protected content',
        'user_id': session_data['user_id']
    })

if __name__ == '__main__':
    # Run the app with an ad hoc SSL context for HTTPS (required for Secure cookies)
    app.run(debug=True, ssl_context='adhoc')
