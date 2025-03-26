import os
import sqlite3
import secrets
import datetime
from flask import Flask, request, redirect, url_for, render_template_string, make_response, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a strong secret key in production
DATABASE = 'app.db'
SESSION_DURATION = datetime.timedelta(hours=1)  # Adjust session duration as needed

def get_db():
    """Return a database connection; one per request."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Close the database connection at the end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Create the necessary tables if they don't exist."""
    db = get_db()
    # Create the users table (for demonstration; assume your real app already has a user DB)
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("DROP TABLE IF EXISTS sessions")
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    ''')
    # Create the sessions table to manage login sessions
    db.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL,
            expires_at DATETIME NOT NULL,
            client_ip TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    ''')
    db.commit()

def create_test_user():
    """Create a test user if one doesn't exist."""
    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE username = ?", ('testuser',))
    user = cur.fetchone()
    if user is None:
        hashed = generate_password_hash('testpass')
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('testuser', hashed))
        db.commit()

@app.before_first_request
def setup():
    """Initialize the DB and create a test user before the first request."""
    init_db()
    create_test_user()

def generate_session_token():
    """Generate a secure session token."""
    return secrets.token_urlsafe(32)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user['password'], password):
            session_token = generate_session_token()
            now = datetime.datetime.utcnow()
            expires_at = now + SESSION_DURATION
            client_ip = request.remote_addr  # Bind the session to the client’s IP address
            db.execute("""
                INSERT INTO sessions (session_token, user_id, created_at, expires_at, client_ip)
                VALUES (?, ?, ?, ?, ?)
            """, (session_token, user['id'], now, expires_at, client_ip))
            db.commit()
            response = make_response(redirect(url_for('protected')))
            # Set the cookie with secure attributes:
            response.set_cookie(
                'session_token',
                session_token,
                httponly=True,        # Prevent JavaScript access
                samesite='Strict',    # Restrict cross-site usage
                secure=False          # Set to True when using HTTPS in production
                # Note: Not setting the domain attribute means it won’t be valid on subdomains.
            )
            return response
        else:
            error = "Invalid credentials. Please try again."
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/logout')
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        db = get_db()
        db.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
        db.commit()
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('session_token')
    return response

def get_current_user():
    """Return the current user session if valid; otherwise, return None."""
    session_token = request.cookies.get('session_token')
    if not session_token:
        return None
    db = get_db()
    cur = db.execute("""
        SELECT s.*, u.username
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE session_token = ?
    """, (session_token,))
    session = cur.fetchone()
    if session:
        now = datetime.datetime.utcnow()
        # Convert stored expiration string back to a datetime object
        expires_at = datetime.datetime.strptime(session['expires_at'], '%Y-%m-%d %H:%M:%S.%f')
        if now > expires_at:
            db.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
            db.commit()
            return None
        # Check client IP to mitigate session theft
        if session['client_ip'] != request.remote_addr:
            return None
        return session
    return None

@app.route('/protected')
def protected():
    user_session = get_current_user()
    if user_session:
        return f"""
            <h2>Hello, {user_session['username']}! You are logged in.</h2>
            <p><a href="{url_for('logout')}">Logout</a></p>
        """
    else:
        return redirect(url_for('login'))

LOGIN_TEMPLATE = '''
<!doctype html>
<html>
  <head>
    <title>Login</title>
  </head>
  <body>
    <h2>Login</h2>
    {% if error %}
      <p style="color:red;">{{ error }}</p>
    {% endif %}
    <form method="post">
      <label for="username">Username:</label>
      <input type="text" name="username" id="username" required>
      <br>
      <label for="password">Password:</label>
      <input type="password" name="password" id="password" required>
      <br>
      <input type="submit" value="Login">
    </form>
  </body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
