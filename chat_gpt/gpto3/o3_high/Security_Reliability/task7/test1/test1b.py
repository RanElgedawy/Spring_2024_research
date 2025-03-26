import sqlite3
import secrets
import datetime
from flask import Flask, request, redirect, url_for, render_template_string, make_response, g, abort
from werkzeug.security import generate_password_hash, check_password_hash

# Configuration
DATABASE = 'database.db'
SESSION_DURATION = datetime.timedelta(minutes=30)  # session expires in 30 minutes

# HTML Templates
HOME_HTML = """
<!doctype html>
<title>Home</title>
<h1>Welcome{% if user %}, {{ user['username'] }}{% endif %}!</h1>
{% if not user %}
  <p><a href="{{ url_for('login') }}">Login</a></p>
{% else %}
  <p><a href="{{ url_for('dashboard') }}">Dashboard (Protected)</a></p>
  <p><a href="{{ url_for('logout') }}">Logout</a></p>
{% endif %}
"""

LOGIN_HTML = """
<!doctype html>
<title>Login</title>
<h1>Login</h1>
<form method="post">
  <label>Username: <input type="text" name="username"></label><br>
  <label>Password: <input type="password" name="password"></label><br>
  <input type="submit" value="Login">
</form>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
"""

DASHBOARD_HTML = """
<!doctype html>
<title>Dashboard</title>
<h1>Dashboard</h1>
<p>Only logged in users can see this.</p>
<p><a href="{{ url_for('home') }}">Home</a></p>
<p><a href="{{ url_for('logout') }}">Logout</a></p>
"""

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)


def get_db():
    """Returns a SQLite database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Closes the DB connection on app context teardown."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    """Initializes the database with required tables."""
    db = get_db()
    with db:
        # Create users table if not exists; for testing we add one user.
        db.execute("DROP TABLE IF EXISTS users")
        db.execute("DROP TABLE IF EXISTS sessions")
        
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
        """)
        # Create sessions table
        db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        # Insert a test user if not exists (username: test, password: password123)
        cur = db.execute("SELECT * FROM users WHERE username = ?", ("test",))
        if cur.fetchone() is None:
            password_hash = generate_password_hash("password123")
            db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("test", password_hash))


def create_session(user_id):
    """Creates a new session for the given user and returns the session token."""
    db = get_db()
    session_id = secrets.token_hex(16)
    now = datetime.datetime.utcnow()
    expires_at = now + SESSION_DURATION
    ip_address = request.remote_addr or "0.0.0.0"
    user_agent = request.headers.get("User-Agent", "unknown")
    with db:
        db.execute("""
            INSERT INTO sessions (session_id, user_id, ip_address, user_agent, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, user_id, ip_address, user_agent, now.isoformat(), expires_at.isoformat()))
    return session_id


def get_session(session_id):
    """Retrieves a valid session from the database if it exists and is valid."""
    db = get_db()
    now = datetime.datetime.utcnow().isoformat()
    cur = db.execute("""
        SELECT * FROM sessions
        WHERE session_id = ? AND expires_at > ?
    """, (session_id, now))
    session = cur.fetchone()
    if session:
        # Optional: enforce that session is used from the same IP and user agent.
        if (session["ip_address"] != (request.remote_addr or "0.0.0.0") or
            session["user_agent"] != request.headers.get("User-Agent", "unknown")):
            return None
    return session


def delete_session(session_id):
    """Deletes a session from the database."""
    db = get_db()
    with db:
        db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))


def get_current_user():
    """Returns the current logged in user if available."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    session = get_session(session_id)
    if not session:
        return None
    # Fetch user info
    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
    return cur.fetchone()


@app.before_first_request
def initialize():
    """Initialize the DB before handling the first request."""
    init_db()


@app.route("/")
def home():
    user = get_current_user()
    return render_template_string(HOME_HTML, user=user)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user["password_hash"], password):
            # Create a new session and set the cookie.
            session_token = create_session(user["id"])
            response = make_response(redirect(url_for("dashboard")))
            response.set_cookie(
                "session_id",
                session_token,
                httponly=True,
                secure=True,  # Set to True in production (requires HTTPS)
                samesite="Strict"  # Cookie won't be sent with cross-site requests
                # Note: We are not setting a domain attribute, so it will only be valid for the current host.
            )
            return response
        else:
            error = "Invalid username or password."
    return render_template_string(LOGIN_HTML, error=error)


@app.route("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template_string(DASHBOARD_HTML)


@app.route("/logout")
def logout():
    session_id = request.cookies.get("session_id")
    if session_id:
        delete_session(session_id)
    response = make_response(redirect(url_for("home")))
    response.set_cookie("session_id", "", expires=0)
    return response


if __name__ == "__main__":
    # Run the Flask development server.
    # Note: In production, you should serve over HTTPS and use a production server.
    app.run(debug=True)
