import sqlite3
import secrets
import datetime
from flask import Flask, request, redirect, make_response, render_template_string, g

# Configuration
DATABASE = 'app.db'
SESSION_DURATION = datetime.timedelta(hours=1)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Templates for demonstration
LOGIN_TEMPLATE = """
<!doctype html>
<title>Login</title>
<h1>Login</h1>
<form method="post">
  <label for="username">Username:</label>
  <input type="text" name="username" id="username" required>
  <br>
  <label for="password">Password:</label>
  <input type="password" name="password" id="password" required>
  <br>
  <input type="submit" value="Login">
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
"""

PROFILE_TEMPLATE = """
<!doctype html>
<title>Profile</title>
<h1>Welcome, {{ username }}!</h1>
<p>This is your protected profile page.</p>
<p><a href="/logout">Logout</a></p>
"""

# Helper functions for database connection and setup
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    # Create users table (if not exists)
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("DROP TABLE IF EXISTS sessions")

    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Create sessions table (if not exists)
    db.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expiry DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    db.commit()
    # Insert a dummy test user if not exists (username: test, password: test)
    cur = db.execute("SELECT * FROM users WHERE username = ?", ("test",))
    if cur.fetchone() is None:
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("test", "test"))
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Session management functions
def create_session(user_id):
    token = secrets.token_urlsafe(32)
    expiry = datetime.datetime.utcnow() + SESSION_DURATION
    db = get_db()
    db.execute("INSERT INTO sessions (token, user_id, expiry) VALUES (?, ?, ?)",
               (token, user_id, expiry.isoformat()))
    db.commit()
    return token

def get_session(token):
    db = get_db()
    cur = db.execute("SELECT * FROM sessions WHERE token = ?", (token,))
    session = cur.fetchone()
    if session:
        expiry = datetime.datetime.fromisoformat(session["expiry"])
        if datetime.datetime.utcnow() > expiry:
            # Session expired; delete it.
            db.execute("DELETE FROM sessions WHERE token = ?", (token,))
            db.commit()
            return None
        return session
    return None

def delete_session(token):
    db = get_db()
    db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    db.commit()

# Route to test login functionality
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        if user:
            token = create_session(user["id"])
            response = make_response(redirect("/profile"))
            # Set cookie without a domain attribute, so it applies only to this domain
            response.set_cookie("session_token", token,
                                httponly=True,
                                secure=False,  # Change to True when using HTTPS
                                samesite="Strict")
            return response
        else:
            error = "Invalid credentials. Please try again."
    return render_template_string(LOGIN_TEMPLATE, error=error)

# Protected route
@app.route('/profile')
def profile():
    token = request.cookies.get("session_token")
    if not token:
        return redirect("/login")
    session = get_session(token)
    if not session:
        return redirect("/login")
    db = get_db()
    cur = db.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],))
    user = cur.fetchone()
    if not user:
        return redirect("/login")
    return render_template_string(PROFILE_TEMPLATE, username=user["username"])

# Logout route
@app.route('/logout')
def logout():
    token = request.cookies.get("session_token")
    if token:
        delete_session(token)
    response = make_response(redirect("/login"))
    response.delete_cookie("session_token")
    return response

# Initialize database before first request
@app.before_first_request
def setup():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
