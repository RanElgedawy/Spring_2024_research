import sqlite3
import uuid
import datetime
from flask import Flask, request, redirect, url_for, g, make_response

app = Flask(__name__)
DATABASE = 'app.db'

# Helper function to get a database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Initialize the database and create tables if they don't exist
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create a table for users
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS sessions")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Create a table for sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE,
                expires_at DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        db.commit()
        # Insert a test user (passwords should be hashed in production)
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                           ("testuser", "testpass"))
            db.commit()
        except sqlite3.IntegrityError:
            # User already exists
            pass

# Close the DB connection on app context teardown
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Create a new session entry and return a session token
def create_session(user_id):
    session_token = str(uuid.uuid4())
    expires_at = datetime.datetime.now() + datetime.timedelta(days=1)  # session valid for 1 day
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)", 
                   (user_id, session_token, expires_at))
    db.commit()
    return session_token

# Validate the session token from the cookie
def validate_session(session_token):
    if not session_token:
        return None
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id, expires_at FROM sessions WHERE session_token = ?", (session_token,))
    row = cursor.fetchone()
    if row:
        user_id, expires_at = row
        # Convert stored expiration string back to a datetime object
        expires_at = datetime.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S.%f")
        if expires_at > datetime.datetime.now():
            return user_id
    return None

# Home endpoint: shows login status and a link to login or logout
@app.route('/')
def index():
    session_token = request.cookies.get('session_token')
    user_id = validate_session(session_token)
    if user_id:
        return f"Logged in as user {user_id}. <a href='/logout'>Logout</a>"
    return "You are not logged in. <a href='/login'>Login</a>"

# Login endpoint: renders a simple form and processes login attempts
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # In production, use secure password storage and validation
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", 
                       (username, password))
        row = cursor.fetchone()
        if row:
            user_id = row[0]
            session_token = create_session(user_id)
            response = make_response(redirect(url_for('index')))
            # Set cookie without a Domain attribute so it's host-only (not valid for subdomains)
            response.set_cookie('session_token', session_token, httponly=True)
            return response
        return "Invalid credentials. <a href='/login'>Try again</a>"
    return '''
        <h2>Login</h2>
        <form method="post">
            Username: <input type="text" name="username" /><br/>
            Password: <input type="password" name="password" /><br/>
            <input type="submit" value="Login" />
        </form>
    '''

# Logout endpoint: clears the session cookie
@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('index')))
    response.delete_cookie('session_token')
    return response

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
