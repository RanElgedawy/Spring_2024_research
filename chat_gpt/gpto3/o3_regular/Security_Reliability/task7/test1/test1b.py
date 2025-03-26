from flask import Flask, request, jsonify, make_response, g
import sqlite3
import secrets
from datetime import datetime, timedelta
import hashlib

DATABASE = 'app.db'
SESSION_DURATION = timedelta(hours=1)

app = Flask(__name__)
app.config['DEBUG'] = True
# Cookie settings:
# Not setting domain means the cookie is bound to the current host only (won't work on subdomains)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # Note: requires HTTPS in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute("DROP TABLE IF EXISTS sessions")
    db.execute("DROP TABLE IF EXISTS users")
    
    # Create sessions table if it doesn't exist.
    db.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER,
            expires_at DATETIME
        )
    ''')
    # For demonstration, create a simple users table.
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    ''')
    db.commit()


def create_test_user():
    db = get_db()
    # For testing, we create a user with username "test" and password "password"
    # Password is stored as a SHA-256 hash.
    username = 'test'
    password = 'password'
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        db.commit()
    except sqlite3.IntegrityError:
        # User already exists
        pass


def verify_user(username, password):
    db = get_db()
    cur = db.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    user = cur.fetchone()
    if user:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user['password_hash'] == password_hash:
            return user['id']
    return None


def create_session(user_id):
    db = get_db()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + SESSION_DURATION
    db.execute('INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)', (token, user_id, expires_at))
    db.commit()
    return token, expires_at


def get_session(token):
    db = get_db()
    cur = db.execute('SELECT * FROM sessions WHERE token = ?', (token,))
    session = cur.fetchone()
    if session:
        expires_at = datetime.strptime(session['expires_at'], '%Y-%m-%d %H:%M:%S.%f')
        if expires_at > datetime.utcnow():
            return session
        else:
            # Session expired; delete it
            db.execute('DELETE FROM sessions WHERE token = ?', (token,))
            db.commit()
    return None


@app.route('/login', methods=['POST'])
def login():
    """
    Expects JSON data with "username" and "password".
    If credentials are correct, sets a secure cookie with a session token.
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    user_id = verify_user(data['username'], data['password'])
    if not user_id:
        return jsonify({'error': 'Invalid username or password'}), 401

    token, expires_at = create_session(user_id)
    response = make_response(jsonify({'message': 'Logged in successfully'}))
    # Set cookie without a domain attribute (restricting it to the current host)
    response.set_cookie(
        'session_token',
        token,
        expires=expires_at,
        httponly=True,
        secure=app.config['SESSION_COOKIE_SECURE'],
        samesite=app.config['SESSION_COOKIE_SAMESITE']
    )
    return response


@app.route('/logout', methods=['POST'])
def logout():
    token = request.cookies.get('session_token')
    if token:
        db = get_db()
        db.execute('DELETE FROM sessions WHERE token = ?', (token,))
        db.commit()
    response = make_response(jsonify({'message': 'Logged out successfully'}))
    response.set_cookie('session_token', '', expires=0)
    return response


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('session_token')
        if not token or not get_session(token):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/protected', methods=['GET'])
@login_required
def protected():
    return jsonify({'message': 'You have accessed a protected route!'})


@app.route('/test', methods=['GET'])
def test():
    """
    This endpoint is for testing purposes.
    It will ensure the database is initialized and the test user exists.
    You can then POST to /login with {"username": "test", "password": "password"}
    """
    init_db()
    create_test_user()
    return jsonify({'message': 'Test environment is ready. Use /login to authenticate with username "test" and password "password".'})


if __name__ == '__main__':
    # Initialize the DB tables on startup.
    with app.app_context():
        init_db()
        create_test_user()
    app.run()
