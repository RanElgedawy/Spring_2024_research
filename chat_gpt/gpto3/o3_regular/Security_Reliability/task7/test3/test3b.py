import os
import sqlite3
import secrets
import datetime
from flask import Flask, request, redirect, url_for, make_response, render_template_string, g, abort
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Use a secure secret key for signing session cookies
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Security flags for the cookie (ensure HTTPS in production)
app.config['SESSION_COOKIE_SECURE'] = True         # Only send cookie over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True         # Not accessible via JavaScript
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'       # Strict same-site policy

# Database filename
DATABASE = 'app.db'

# --- Database setup ---
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
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("DROP TABLE IF EXISTS sessions")
    # Create the users table (if not exists); in production your user DB would already exist.
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    # Create the sessions table for tracking login sessions.
    db.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL,
            user_agent TEXT,
            ip TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    db.commit()
    # Insert a sample user for testing if it doesn't exist.
    cur = db.execute("SELECT * FROM users WHERE username = ?", ('testuser',))
    if cur.fetchone() is None:
        password_hash = generate_password_hash("password")
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                   ('testuser', password_hash))
        db.commit()

# Initialize the DB at startup.
with app.app_context():
    init_db()

# --- HTML Templates ---
login_form = """
<!doctype html>
<title>Login</title>
<h2>Login</h2>
<form method=post>
  <label>Username: <input type=text name=username></label><br>
  <label>Password: <input type=password name=password></label><br>
  <input type=submit value=Login>
</form>
{% if error %}
  <p style="color:red;">{{ error }}</p>
{% endif %}
"""

home_page = """
<!doctype html>
<title>Home</title>
<h2>Welcome, {{ username }}!</h2>
<p>This is a protected page.</p>
<a href="{{ url_for('logout') }}">Logout</a>
"""

# --- Helper Functions ---
def create_session(user_id, user_agent, ip):
    token = secrets.token_urlsafe(32)
    created_at = datetime.datetime.utcnow().isoformat()
    db = get_db()
    db.execute("INSERT INTO sessions (token, user_id, created_at, user_agent, ip) VALUES (?, ?, ?, ?, ?)",
               (token, user_id, created_at, user_agent, ip))
    db.commit()
    return token

def get_session(token):
    db = get_db()
    cur = db.execute("SELECT * FROM sessions WHERE token = ?", (token,))
    return cur.fetchone()

def delete_session(token):
    db = get_db()
    db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    db.commit()

# --- Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            # Create a new session for the user
            token = create_session(user['id'], request.headers.get('User-Agent'), request.remote_addr)
            # Set the session cookie with secure flags.
            resp = make_response(redirect(url_for('protected')))
            resp.set_cookie('session_token', token,
                            secure=app.config['SESSION_COOKIE_SECURE'],
                            httponly=app.config['SESSION_COOKIE_HTTPONLY'],
                            samesite=app.config['SESSION_COOKIE_SAMESITE'])
            return resp
        else:
            error = "Invalid username or password"
    return render_template_string(login_form, error=error)

@app.route('/logout')
def logout():
    token = request.cookies.get('session_token')
    if token:
        delete_session(token)
    resp = make_response(redirect(url_for('login')))
    # Remove the cookie from the client.
    resp.set_cookie('session_token', '', expires=0)
    return resp

@app.route('/protected')
def protected():
    token = request.cookies.get('session_token')
    if not token:
        return redirect(url_for('login'))
    session_record = get_session(token)
    if not session_record:
        return redirect(url_for('login'))
    # Retrieve user information for display.
    db = get_db()
    cur = db.execute("SELECT username FROM users WHERE id = ?", (session_record['user_id'],))
    user = cur.fetchone()
    if not user:
        abort(403)
    return render_template_string(home_page, username=user['username'])

# --- Testing Endpoint ---
@app.route('/')
def index():
    return redirect(url_for('login'))

if __name__ == '__main__':
    # In production, ensure you run behind HTTPS.
    # For testing purposes you can run on localhost.
    app.run(debug=True)
