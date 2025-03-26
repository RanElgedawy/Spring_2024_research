import os
import sqlite3
import secrets
import datetime
from flask import Flask, request, redirect, url_for, render_template_string, make_response, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'replace-with-a-secure-secret-key'  # Replace this with a proper secret key in production

DATABASE = './app.db'
SESSION_COOKIE_NAME = 'session_token'
SESSION_EXPIRY_MINUTES = 60  # Session expiration after 60 minutes of inactivity

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initializes the database by creating the required tables if they do not exist."""
    db = get_db()
    # Create users table (for demonstration; assume this exists in your real app)
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("DROP TAbLE IF EXISTS sessions")
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    # Create sessions table to manage login sessions
    db.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            user_agent TEXT,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    db.commit()

def create_default_user():
    """Creates a default user if it doesn't already exist."""
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE username = ?', ('testuser',))
    if cur.fetchone() is None:
        password_hash = generate_password_hash('testpass')
        db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('testuser', password_hash))
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def create_session(user_id, user_agent):
    """Generates a session token, stores it in the DB along with the user’s ID and User-Agent."""
    db = get_db()
    session_token = secrets.token_hex(32)
    created_at = datetime.datetime.utcnow()
    db.execute('INSERT INTO sessions (session_token, user_id, user_agent, created_at) VALUES (?, ?, ?, ?)',
               (session_token, user_id, user_agent, created_at))
    db.commit()
    return session_token

def get_session(session_token, current_user_agent):
    """Retrieves and validates the session from the DB.
    
    Checks:
      - Session exists.
      - Session has not expired.
      - User-Agent matches to help mitigate cookie theft.
    """
    db = get_db()
    cur = db.execute('SELECT * FROM sessions WHERE session_token = ?', (session_token,))
    session = cur.fetchone()
    if session is None:
        return None
    # Check if session expired
    created_at = datetime.datetime.strptime(session['created_at'], '%Y-%m-%d %H:%M:%S.%f')
    if datetime.datetime.utcnow() - created_at > datetime.timedelta(minutes=SESSION_EXPIRY_MINUTES):
        delete_session(session_token)
        return None
    # Validate the User-Agent for extra security
    if session['user_agent'] != current_user_agent:
        return None
    return session

def delete_session(session_token):
    """Deletes the session from the database."""
    db = get_db()
    db.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
    db.commit()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_agent = request.headers.get('User-Agent')
        db = get_db()
        cur = db.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cur.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            # Valid credentials; create a new session
            session_token = create_session(user['id'], user_agent)
            response = make_response(redirect(url_for('dashboard')))
            # Set cookie with secure flags; note: secure=True requires HTTPS in production
            response.set_cookie(SESSION_COOKIE_NAME, session_token,
                                httponly=True,
                                samesite='Strict',
                                secure=True)
            return response
        else:
            error = 'Invalid username or password'
    # Render a simple login form
    return render_template_string('''
        <h2>Login</h2>
        {% if error %}
          <p style="color:red;">{{ error }}</p>
        {% endif %}
        <form method="post">
            Username: <input type="text" name="username" required><br><br>
            Password: <input type="password" name="password" required><br><br>
            <input type="submit" value="Login">
        </form>
    ''', error=error)

@app.route('/dashboard')
def dashboard():
    """A protected route that requires a valid session."""
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        return redirect(url_for('login'))
    user_agent = request.headers.get('User-Agent')
    session = get_session(session_token, user_agent)
    if not session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cur.fetchone()
    return render_template_string('''
        <h2>Dashboard</h2>
        <p>Welcome, {{ user['username'] }}!</p>
        <p>Your session is active.</p>
        <a href="{{ url_for('logout') }}">Logout</a>
    ''', user=user)

@app.route('/logout')
def logout():
    """Logs out the user by deleting the session and clearing the cookie."""
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        delete_session(session_token)
    response = make_response(redirect(url_for('login')))
    response.set_cookie(SESSION_COOKIE_NAME, '', expires=0)
    return response

if __name__ == '__main__':
    with app.app_context():
        init_db()
        create_default_user()
    app.run(debug=True)
