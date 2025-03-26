from flask import Flask, request, redirect, url_for, make_response, render_template_string, g
import sqlite3
import uuid
import datetime

app = Flask(__name__)
DATABASE = 'app.db'

# Helper function to get a database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

# Close the DB connection when the context ends
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize the database tables if they do not exist
def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS sessions")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at DATETIME NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    db.commit()

# Create a test user if one doesn't exist
def create_test_user():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", ("testuser",))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("testuser", "password"))
        db.commit()

# Setup: create tables and test user before the first request
@app.before_first_request
def setup():
    init_db()
    create_test_user()

# Login endpoint (GET shows form, POST processes login)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        if user:
            # Generate a new session token and set expiration (30 minutes)
            session_token = str(uuid.uuid4())
            expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
            cursor.execute("INSERT INTO sessions (session_id, user_id, expires_at) VALUES (?, ?, ?)",
                           (session_token, user['id'], expires))
            db.commit()
            response = make_response(redirect(url_for('dashboard')))
            # Set cookie without specifying the domain makes it host-only.
            response.set_cookie('session_token', session_token,
                                httponly=True, samesite='Strict', expires=expires)
            return response
        else:
            return "Invalid credentials", 401
    return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            Username: <input type="text" name="username" /><br/>
            Password: <input type="password" name="password" /><br/>
            <input type="submit" value="Login" />
        </form>
    ''')

# Logout endpoint: removes the session from the DB and clears the cookie
@app.route('/logout')
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        db = get_db()
        db.execute("DELETE FROM sessions WHERE session_id = ?", (session_token,))
        db.commit()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session_token', '', expires=0)
    return response

# Helper function to get the current user based on the session cookie
def get_current_user():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return None
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_token,))
    session = cursor.fetchone()
    if session:
        # Check if the session has expired
        expires_at = datetime.datetime.strptime(session['expires_at'], "%Y-%m-%d %H:%M:%S.%f")
        if expires_at > datetime.datetime.utcnow():
            cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
            user = cursor.fetchone()
            return user
        else:
            db.execute("DELETE FROM sessions WHERE session_id = ?", (session_token,))
            db.commit()
    return None

# Protected endpoint: only accessible if logged in
@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    return f"Welcome {user['username']}! <br/><a href='/logout'>Logout</a>"

# Default route: redirect based on session validity
@app.route('/')
def index():
    user = get_current_user()
    if user:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
