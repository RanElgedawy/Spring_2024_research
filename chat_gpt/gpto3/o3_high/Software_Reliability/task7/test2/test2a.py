import sqlite3
import uuid
from flask import Flask, request, redirect, url_for, make_response, render_template_string, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
DATABASE = 'app.db'

# ---------------------
# Database Helper Functions
# ---------------------
def get_db():
    """Get a connection to the database, creating it if necessary."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # To access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Create the necessary tables if they do not exist."""
    db = get_db()
    cur = db.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS sessions")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    db.commit()

def create_sample_user():
    """Insert a sample user if not already present."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", ("test",))
    if cur.fetchone() is None:
        # The sample user has username 'test' and password 'password'
        hashed = generate_password_hash("password")
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("test", hashed))
        db.commit()

# ---------------------
# Authentication Helpers
# ---------------------
def login_required(f):
    """Decorator that checks for a valid session cookie."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get('session_id')
        if not session_id:
            return redirect(url_for('login'))
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        session = cur.fetchone()
        if session is None:
            return redirect(url_for('login'))
        # Retrieve user information for use in the endpoint
        cur.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = cur.fetchone()
        if user is None:
            return redirect(url_for('login'))
        # Save the user info in Flask's global context
        g.user = user
        return f(*args, **kwargs)
    return decorated_function

# ---------------------
# Routes
# ---------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            # Valid credentials – generate a session token
            session_id = str(uuid.uuid4())
            cur.execute("INSERT INTO sessions (session_id, user_id) VALUES (?, ?)", (session_id, user['id']))
            db.commit()
            response = make_response(redirect(url_for('protected')))
            # Set cookie without specifying 'domain'; by default, it will only be sent to the current host.
            response.set_cookie('session_id', session_id, httponly=True)
            return response
        else:
            return "Invalid credentials", 401
    else:
        # Provide a simple login form for testing
        return render_template_string('''
            <h2>Login</h2>
            <form method="post">
                Username: <input type="text" name="username" required><br>
                Password: <input type="password" name="password" required><br>
                <input type="submit" value="Login">
            </form>
            <p>Try logging in with username <strong>test</strong> and password <strong>password</strong>.</p>
        ''')

@app.route('/protected')
@login_required
def protected():
    """A protected page that only logged-in users can access."""
    return f"Hello, {g.user['username']}! You are logged in."

@app.route('/logout')
@login_required
def logout():
    """Log out the current user by deleting the session and clearing the cookie."""
    session_id = request.cookies.get('session_id')
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    db.commit()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session_id', '', expires=0)
    return response

# ---------------------
# Application Startup
# ---------------------
@app.before_first_request
def setup():
    """Initialize the database and insert a sample user before handling any requests."""
    init_db()
    create_sample_user()

if __name__ == '__main__':
    # Run the app (use debug mode for testing)
    app.run(debug=True)
