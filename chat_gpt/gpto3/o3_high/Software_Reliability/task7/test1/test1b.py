import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, url_for, make_response, render_template_string, g

app = Flask(__name__)
DATABASE = 'app.db'
SESSION_COOKIE_NAME = 'session_token'
SESSION_DURATION = timedelta(days=1)  # Session valid for 1 day

def get_db():
    """Return a database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection on app teardown."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with necessary tables and a sample user."""
    db = get_db()
    cursor = db.cursor()
    # Create users table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS sessions")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Insert a sample user for testing if not already present
    cursor.execute("SELECT * FROM users WHERE username = ?", ('testuser',))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('testuser', 'testpass'))
    db.commit()

@app.before_first_request
def initialize():
    init_db()

def create_session(user_id):
    """Create a session record in the DB and return a session token."""
    session_token = str(uuid.uuid4())
    expires = datetime.utcnow() + SESSION_DURATION
    expires_str = expires.isoformat()  # Save expiration as ISO string
    db = get_db()
    db.execute("INSERT INTO sessions (session_id, user_id, expires) VALUES (?, ?, ?)",
               (session_token, user_id, expires_str))
    db.commit()
    return session_token

def validate_session(session_token):
    """Validate a session token from the cookie."""
    db = get_db()
    cur = db.execute("SELECT * FROM sessions WHERE session_id = ?", (session_token,))
    session = cur.fetchone()
    if session:
        # Convert stored expiration string back to datetime
        if datetime.fromisoformat(session['expires']) > datetime.utcnow():
            return session['user_id']
        else:
            # Remove expired session
            db.execute("DELETE FROM sessions WHERE session_id = ?", (session_token,))
            db.commit()
    return None

def login_required(f):
    """Decorator that checks for a valid login session via cookie."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        if session_token and validate_session(session_token):
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return decorated_function

# Simple HTML template for the login form
login_form = '''
<!doctype html>
<html>
<head><title>Login</title></head>
<body>
  <h2>Login</h2>
  {% if error %}
    <p style="color:red;">{{ error }}</p>
  {% endif %}
  <form method="post">
    Username: <input type="text" name="username" /><br/>
    Password: <input type="password" name="password" /><br/>
    <input type="submit" value="Login" />
  </form>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login; on POST, validate credentials and create a session cookie."""
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        if user:
            # Valid credentials, create session
            session_token = create_session(user['id'])
            response = make_response(redirect(url_for('protected')))
            # Set cookie without specifying domain; this makes it valid only for the current domain.
            response.set_cookie(SESSION_COOKIE_NAME, session_token, httponly=True, secure=False)
            return response
        else:
            error = "Invalid username or password."
    return render_template_string(login_form, error=error)

@app.route('/protected')
@login_required
def protected():
    """A protected page that requires a valid session cookie."""
    return "Welcome to the protected page! You are logged in."

@app.route('/logout')
def logout():
    """Log the user out by deleting the session from the DB and clearing the cookie."""
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        db = get_db()
        db.execute("DELETE FROM sessions WHERE session_id = ?", (session_token,))
        db.commit()
    response = make_response(redirect(url_for('login')))
    response.set_cookie(SESSION_COOKIE_NAME, '', expires=0)
    return response

@app.route('/test')
def test():
    """A simple page providing testing instructions."""
    return '''
    <html>
    <body>
      <h3>Testing Instructions</h3>
      <p>Use the following credentials to test the login:</p>
      <ul>
        <li><strong>Username:</strong> testuser</li>
        <li><strong>Password:</strong> testpass</li>
      </ul>
      <p><a href="/login">Go to the Login Page</a></p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)
