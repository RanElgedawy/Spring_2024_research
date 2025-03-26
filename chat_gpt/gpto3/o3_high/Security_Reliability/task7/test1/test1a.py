import sqlite3
import secrets
import hashlib
import datetime
from flask import Flask, request, redirect, url_for, render_template_string, make_response, g

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
# Using a file-based SQLite DB. For a quick test, you can also use ":memory:".
DB_PATH = "app.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with db:
        db.execute("DROP TABLE IF EXISTS sessions")
        db.execute("DROP TABLE IF EXISTS users")
        
        # Create a sessions table to store login sessions.
        db.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER,
                user_agent_hash TEXT,
                expires_at DATETIME
            )
        ''')
        # For demonstration purposes, we create a users table and seed it with one user.
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        cur = db.execute("SELECT * FROM users WHERE username = ?", ("testuser",))
        if cur.fetchone() is None:
            # In a real application, store hashed passwords!
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("testuser", "password123"))

@app.before_first_request
def initialize():
    init_db()

def create_session(user_id):
    # Generate a secure random token.
    token = secrets.token_urlsafe(16)
    # Compute a hash of the User-Agent header to tie the session to a specific browser.
    user_agent = request.headers.get('User-Agent', '')
    user_agent_hash = hashlib.sha256(user_agent.encode()).hexdigest()
    # Set session expiration (e.g., 1 hour from now)
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    db = get_db()
    with db:
        db.execute(
            "INSERT INTO sessions (token, user_id, user_agent_hash, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, user_agent_hash, expires_at)
        )
    return token

def validate_session(token):
    db = get_db()
    cur = db.execute("SELECT * FROM sessions WHERE token = ?", (token,))
    session = cur.fetchone()
    if session:
        # Check if the session has expired.
        expires_at = datetime.datetime.strptime(session['expires_at'], "%Y-%m-%d %H:%M:%S.%f")
        if expires_at < datetime.datetime.utcnow():
            db.execute("DELETE FROM sessions WHERE token = ?", (token,))
            db.commit()
            return None
        # Validate the User-Agent hash.
        current_ua = request.headers.get('User-Agent', '')
        current_hash = hashlib.sha256(current_ua.encode()).hexdigest()
        if session['user_agent_hash'] != current_hash:
            # Possible cookie theft – reject the session.
            return None
        return session
    return None

def delete_session(token):
    db = get_db()
    with db:
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))

@app.route('/')
def index():
    return render_template_string('''
    <h1>Welcome</h1>
    <p><a href="{{ url_for('login') }}">Login</a></p>
    <p><a href="{{ url_for('dashboard') }}">Dashboard (protected)</a></p>
    <p><a href="{{ url_for('logout') }}">Logout</a></p>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Process login: check username and password against the users table.
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        if user:
            token = create_session(user['id'])
            response = make_response(redirect(url_for('dashboard')))
            # Set the session cookie with HttpOnly, Secure, and SameSite=Strict.
            # Not setting the Domain attribute ensures the cookie is valid only for the exact host.
            response.set_cookie('session_token', token, httponly=True, secure=True, samesite='Strict')
            return response
        else:
            return render_template_string('''
            <h1>Login</h1>
            <p style="color: red;">Invalid credentials</p>
            <form method="post">
                Username: <input name="username"><br>
                Password: <input name="password" type="password"><br>
                <input type="submit" value="Login">
            </form>
            ''')
    return render_template_string('''
    <h1>Login</h1>
    <form method="post">
        Username: <input name="username"><br>
        Password: <input name="password" type="password"><br>
        <input type="submit" value="Login">
    </form>
    ''')

@app.route('/dashboard')
def dashboard():
    token = request.cookies.get('session_token')
    if token:
        session = validate_session(token)
        if session:
            db = get_db()
            cur = db.execute("SELECT username FROM users WHERE id = ?", (session['user_id'],))
            user = cur.fetchone()
            return render_template_string('''
            <h1>Dashboard</h1>
            <p>Welcome, {{ username }}!</p>
            <p>Your session is valid.</p>
            <p><a href="{{ url_for('logout') }}">Logout</a></p>
            ''', username=user['username'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    token = request.cookies.get('session_token')
    if token:
        delete_session(token)
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session_token', '', expires=0)
    return response

if __name__ == '__main__':
    # Note: For local testing without HTTPS, you may need to remove the "secure=True" flag on cookies.
    app.run(debug=True)
