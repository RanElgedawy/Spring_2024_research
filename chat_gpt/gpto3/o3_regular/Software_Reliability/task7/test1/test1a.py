import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, g, make_response

app = Flask(__name__)
DATABASE = 'app.db'

# ----- Database Utilities -----
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # connect to SQLite database file
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    cur.close()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ----- Database Setup -----
def init_db():
    with app.app_context():
        db = get_db()
        # Create users table
        db.execute("DROP TABLE IF EXISTS users")
        db.execute("DROP TABLE IF EXISTS sessions")

        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Create sessions table
        db.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # Insert a test user if not exists
        user = query_db("SELECT * FROM users WHERE username = ?", ("testuser",), one=True)
        if not user:
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("testuser", "test123"))
        db.commit()

init_db()

# ----- Helper Functions -----
def create_session(user_id):
    token = str(uuid.uuid4())
    created_at = datetime.utcnow()
    execute_db("INSERT INTO sessions (user_id, session_token, created_at) VALUES (?, ?, ?)",
               (user_id, token, created_at))
    return token

def validate_session(token):
    session = query_db("SELECT * FROM sessions WHERE session_token = ?", (token,), one=True)
    if session:
        # Optionally, add expiration check here (for example, valid for 24 hours)
        return session['user_id']
    return None

# ----- Routes -----
@app.route('/login', methods=['POST'])
def login():
    """
    Expects JSON with "username" and "password".
    If valid, creates a session and sets a cookie for the current domain.
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400

    user = query_db("SELECT * FROM users WHERE username = ? AND password = ?",
                    (data['username'], data['password']), one=True)
    if user is None:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Create session token
    token = create_session(user['id'])
    response = make_response(jsonify({'message': 'Login successful'}))
    # Set cookie without specifying a domain, so it applies only to the current domain (not subdomains)
    response.set_cookie(
        'session_token', token,
        httponly=True,
        secure=False,      # Change to True if using HTTPS
        samesite='Lax',    # Prevent CSRF in a basic way
        path='/'
    )
    return response

@app.route('/protected', methods=['GET'])
def protected():
    """
    A sample route that requires a valid login session.
    """
    token = request.cookies.get('session_token')
    if not token:
        return jsonify({'error': 'Authentication required'}), 401

    user_id = validate_session(token)
    if not user_id:
        return jsonify({'error': 'Invalid or expired session'}), 401

    user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
    return jsonify({
        'message': 'Access granted to protected content',
        'user': user['username']
    })

# ----- Testing Endpoint -----
@app.route('/')
def index():
    """
    Simple home page with instructions for testing.
    """
    return """
    <h1>Welcome to the Test Login App</h1>
    <p>To test the login functionality:</p>
    <ul>
      <li>POST JSON to /login with {"username": "testuser", "password": "test123"}</li>
      <li>Then GET /protected with the session cookie.</li>
    </ul>
    """

if __name__ == '__main__':
    app.run(debug=True)
