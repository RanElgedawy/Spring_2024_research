from flask import Flask, request, redirect, url_for, make_response
import sqlite3
import uuid
import datetime

app = Flask(__name__)
DB_PATH = 'app.db'

def init_db():
    """Initializes the database and creates necessary tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Create users table if it doesn't exist.
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS sessions")

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Create sessions table to store login sessions.
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Insert a test user (if not already present).
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("test", "password"))
    conn.commit()
    conn.close()

# Initialize database on startup.
init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_session(user_id):
    """Creates a new session for a user and returns the session token."""
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO sessions (session_id, user_id, created_at) VALUES (?, ?, ?)",
              (session_id, user_id, datetime.datetime.utcnow()))
    conn.commit()
    conn.close()
    return session_id

def get_user_from_session(session_id):
    """Retrieves user info based on a session token."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT users.* 
        FROM sessions JOIN users ON sessions.user_id = users.id 
        WHERE session_id = ?
    """, (session_id,))
    user = c.fetchone()
    conn.close()
    return user

def delete_session(session_id):
    """Deletes a session from the database."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Home page shows different content based on login state."""
    session_id = request.cookies.get('session_id')
    if session_id:
        user = get_user_from_session(session_id)
        if user:
            return f"Hello, {user['username']}! <br><a href='/logout'>Logout</a> <br><a href='/protected'>Protected Page</a>"
    return "Hello, Guest! <br><a href='/login'>Login</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve username and password from the submitted form.
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            # Valid login: create session and set a cookie.
            session_id = create_session(user['id'])
            resp = make_response(redirect(url_for('index')))
            # Set cookie with HttpOnly and SameSite attributes.
            # Not setting the 'domain' attribute ensures the cookie is valid only for the current host.
            resp.set_cookie('session_id', session_id, httponly=True, samesite='Lax')
            return resp
        else:
            return "Invalid credentials. <a href='/login'>Try again</a>"
    # Simple HTML form for login.
    return '''
        <h2>Login</h2>
        <form method="post">
            Username: <input type="text" name="username" /><br>
            Password: <input type="password" name="password" /><br>
            <input type="submit" value="Login" />
        </form>
    '''

@app.route('/logout')
def logout():
    """Logs the user out by deleting the session and clearing the cookie."""
    session_id = request.cookies.get('session_id')
    if session_id:
        delete_session(session_id)
    resp = make_response(redirect(url_for('index')))
    # Clear the cookie by setting it to an empty value with an expiration in the past.
    resp.set_cookie('session_id', '', expires=0)
    return resp

@app.route('/protected')
def protected():
    """A protected route that only logged in users can access."""
    session_id = request.cookies.get('session_id')
    if session_id:
        user = get_user_from_session(session_id)
        if user:
            return f"Welcome to the protected page, {user['username']}!"
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
