import os
import uuid
import datetime
import sqlite3
from flask import Flask, request, redirect, url_for, make_response, render_template_string, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Set a secret key for session management and signing cookies.
app.secret_key = os.urandom(24)

DATABASE = 'app.db'

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initializes the database by creating the required tables and a test user."""
    with app.app_context():
        db = get_db()
        db.execute("DROP TABLE IF EXISTS users")
        db.execute("DROP TABLE IF EXISTS sessions")
        
        # Create users table (simulate your existing user database)
        db.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                      )''')
        # Create sessions table for login sessions
        db.execute('''CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_token TEXT UNIQUE NOT NULL,
                        user_id INTEGER NOT NULL,
                        expiry DATETIME NOT NULL,
                        client_ip TEXT,
                        user_agent TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                      )''')
        db.commit()
        
        # Insert a test user if it doesn't already exist.
        cur = db.execute("SELECT * FROM users WHERE username = ?", ("testuser",))
        if not cur.fetchone():
            hashed_password = generate_password_hash("testpass")
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       ("testuser", hashed_password))
            db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def create_session(user_id):
    """Creates a session for the given user id and returns a secure session token."""
    db = get_db()
    token = uuid.uuid4().hex
    expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    # Format expiry as a string so we can store it in SQLite.
    expiry_str = expiry.strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    db.execute("""INSERT INTO sessions (session_token, user_id, expiry, client_ip, user_agent)
                  VALUES (?, ?, ?, ?, ?)""",
               (token, user_id, expiry_str, client_ip, user_agent))
    db.commit()
    return token

def get_session(token):
    """Retrieves and validates the session from the database based on the token."""
    db = get_db()
    cur = db.execute("SELECT * FROM sessions WHERE session_token = ?", (token,))
    session = cur.fetchone()
    if session:
        # Check if the session has expired.
        expiry = datetime.datetime.strptime(session["expiry"], "%Y-%m-%d %H:%M:%S")
        if expiry < datetime.datetime.utcnow():
            db.execute("DELETE FROM sessions WHERE session_token = ?", (token,))
            db.commit()
            return None
        # Extra protection: verify the client IP and user-agent match.
        if session["client_ip"] != request.remote_addr or session["user_agent"] != request.headers.get('User-Agent'):
            return None
    return session

def delete_session(token):
    """Deletes the session corresponding to the given token."""
    db = get_db()
    db.execute("DELETE FROM sessions WHERE session_token = ?", (token,))
    db.commit()

def login_required(f):
    """A decorator to protect routes that require a valid login session."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("session_token")
        if not token or not get_session(token):
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# HTML templates for login and protected pages
login_page_html = '''
<!doctype html>
<title>Login</title>
<h2>Login</h2>
<form method="post">
  Username: <input type="text" name="username"><br>
  Password: <input type="password" name="password"><br>
  <input type="submit" value="Login">
</form>
{% if error %}
  <p style="color: red;">{{ error }}</p>
{% endif %}
'''

protected_page_html = '''
<!doctype html>
<title>Protected</title>
<h2>Welcome, {{ username }}!</h2>
<p>This is a protected page.</p>
<p><a href="{{ url_for('logout') }}">Logout</a></p>
'''

@app.route('/')
def index():
    return '<h1>Welcome to the E-commerce Site</h1><p><a href="/login">Login</a> to access your account.</p>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user["password"], password):
            # Credentials are valid; create a new session.
            token = create_session(user["id"])
            response = make_response(redirect(url_for('protected')))
            # Set the cookie with security flags:
            # - Not setting a 'domain' attribute makes it host-only (won't work for subdomains).
            # - HttpOnly prevents JavaScript access.
            # - Secure ensures the cookie is only sent over HTTPS.
            # - SameSite="Strict" prevents cross-site request forgery.
            response.set_cookie("session_token", token, httponly=True, secure=True, samesite="Strict")
            return response
        else:
            error = "Invalid username or password"
    return render_template_string(login_page_html, error=error)

@app.route('/protected')
@login_required
def protected():
    token = request.cookies.get("session_token")
    session = get_session(token)
    if session:
        db = get_db()
        cur = db.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],))
        user = cur.fetchone()
        if user:
            return render_template_string(protected_page_html, username=user["username"])
    return redirect(url_for("login"))

@app.route('/logout')
def logout():
    token = request.cookies.get("session_token")
    if token:
        delete_session(token)
    response = make_response(redirect(url_for("index")))
    response.set_cookie("session_token", '', expires=0)
    return response

if __name__ == '__main__':
    init_db()
    # IMPORTANT: In production, serve this app over HTTPS so the Secure cookie flag is effective.
    app.run(debug=True)
