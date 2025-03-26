from flask import Flask, request, make_response, redirect, url_for, abort
from datetime import datetime, timedelta
import secrets
import sqlite3
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': secrets.token_hex(32),
    'DATABASE': 'sessions.db',
    'SESSION_DURATION': 3600,  # 1 hour in seconds
    'SERVER_NAME': 'localhost:5000'  # Add explicit server name for testing
})

# Database setup with explicit cleanup
def init_db():
    with sqlite3.connect(app.config['DATABASE']) as conn:
        conn.execute("DROP TABLE IF EXISTS sessions")
        conn.execute("DROP TABLE IF EXISTS users")
        
        conn.execute('''
            CREATE TABLE sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                user_agent_hash TEXT,
                ip_address TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        # Create test user
        conn.execute('''
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        ''', ('test', generate_password_hash('testpassword')))
        conn.commit()

init_db()

def get_db():
    return sqlite3.connect(app.config['DATABASE'])

# Security helpers
def generate_session_token():
    return secrets.token_hex(32)

def hash_user_agent(user_agent):
    return hashlib.sha256(user_agent.encode()).hexdigest()

# Session management
def create_session(user_id, user_agent, ip_address):
    session_id = generate_session_token()
    expires_at = datetime.now() + timedelta(seconds=app.config['SESSION_DURATION'])
    
    with get_db() as conn:
        conn.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
        conn.execute('''
            INSERT INTO sessions (session_id, user_id, expires_at, user_agent_hash, ip_address)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_id, expires_at, hash_user_agent(user_agent), ip_address))
        conn.commit()
    
    return session_id

def validate_session(session_id, user_agent, ip_address):
    with get_db() as conn:
        session = conn.execute('''
            SELECT * FROM sessions 
            WHERE session_id = ? AND expires_at > ?
        ''', (session_id, datetime.now())).fetchone()
    
    if not session:
        return False
    
    if hash_user_agent(user_agent) != session[3]:
        return False
    
    return session[1]

# Test routes
@app.route('/test_login', methods=['GET'])
def test_login():
    """Direct login for testing purposes"""
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE username = "test"').fetchone()
    
    session_id = create_session(
        user_id=user[0],
        user_agent='TestAgent/1.0',
        ip_address='127.0.0.1'
    )
    
    response = make_response(f"Test login successful! Session: {session_id}")
    response.set_cookie(
        'session_id',
        value=session_id,
        max_age=app.config['SESSION_DURATION'],
        secure=False,
        httponly=True,
        samesite='Lax'
    )
    return response

@app.route('/test_session')
def test_session():
    """Session validation test endpoint"""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return "No session found", 401
    
    user_id = validate_session(
        session_id,
        user_agent=request.headers.get('User-Agent', 'TestAgent/1.0'),
        ip_address=request.remote_addr
    )
    
    if user_id:
        return f"Valid session for user {user_id}"
    return "Invalid session", 401

# Main application routes
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    
    if user and check_password_hash(user[2], password):
        session_id = create_session(
            user_id=user[0],
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        
        response = make_response(redirect(url_for('dashboard')))
        response.set_cookie(
            'session_id',
            value=session_id,
            max_age=app.config['SESSION_DURATION'],
            secure=False,
            httponly=True,
            samesite='Lax'
        )
        return response
    
    return abort(401)

@app.route('/logout')
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        with get_db() as conn:
            conn.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            conn.commit()
    
    response = make_response(redirect(url_for('login_page')))
    response.set_cookie('session_id', '', expires=0)
    return response

@app.route('/dashboard')
def dashboard():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return redirect(url_for('login_page'))
    
    user_id = validate_session(
        session_id,
        user_agent=request.headers.get('User-Agent'),
        ip_address=request.remote_addr
    )
    
    if not user_id:
        return redirect(url_for('login_page'))
    
    return f"Welcome to your dashboard! User ID: {user_id}"

@app.route('/')
def login_page():
    return '''
        <form method="post" action="/login">
            <input type="text" name="username" placeholder="Username" value="test">
            <input type="password" name="password" placeholder="Password" value="testpassword">
            <button type="submit">Login</button>
        </form>
        <hr>
        <a href="/test_login">Test Login (auto-authenticate)</a>
    '''

if __name__ == '__main__':
    app.run(
        # ssl_context='adhoc',
        host='0.0.0.0',
        port=5000,
        debug=True
    )