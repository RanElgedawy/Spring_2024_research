from flask import Flask, request, redirect, url_for, make_response, render_template_string, g
import sqlite3
import secrets
import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

DATABASE = "app.db"

# ---------------- Database Utilities ----------------

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Connect to SQLite database (creates file if not exists)
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        # Create users table
        db.execute("DROP TABLE IF EXISTS users")
        db.execute("DROP TABLE IF EXISTS sessions")
        
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Create sessions table for storing session tokens
        db.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ---------------- Helper Functions ----------------

def create_session(user_id):
    token = secrets.token_urlsafe(32)
    db = get_db()
    db.execute('INSERT INTO sessions (token, user_id) VALUES (?, ?)', (token, user_id))
    db.commit()
    return token

def get_user_by_session(token):
    db = get_db()
    cur = db.execute('''
        SELECT users.id, users.username 
        FROM users JOIN sessions ON users.id = sessions.user_id 
        WHERE sessions.token = ?
    ''', (token,))
    return cur.fetchone()

def delete_session(token):
    db = get_db()
    db.execute('DELETE FROM sessions WHERE token = ?', (token,))
    db.commit()

# ---------------- Routes ----------------

# A simple home page with links
@app.route('/')
def index():
    return render_template_string('''
        <h1>E-commerce Demo</h1>
        <ul>
            <li><a href="{{ url_for('register') }}">Register (for testing)</a></li>
            <li><a href="{{ url_for('login') }}">Login</a></li>
            <li><a href="{{ url_for('dashboard') }}">Dashboard (Protected)</a></li>
            <li><a href="{{ url_for('logout') }}">Logout</a></li>
        </ul>
    ''')

# Registration route (for testing purposes)
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            db.commit()
            msg = 'User registered successfully!'
        except sqlite3.IntegrityError:
            msg = 'Username already exists.'
    return render_template_string('''
        <h2>Register</h2>
        <form method="post">
            Username: <input type="text" name="username" required/><br/>
            Password: <input type="password" name="password" required/><br/>
            <input type="submit" value="Register"/>
        </form>
        <p>{{msg}}</p>
        <a href="{{ url_for('index') }}">Back to Home</a>
    ''', msg=msg)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cur = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cur.fetchone()
        if user:
            token = create_session(user['id'])
            response = make_response(redirect(url_for('dashboard')))
            # Set cookie without the 'domain' attribute to ensure it is host-only.
            response.set_cookie('session_token', token, httponly=True, samesite='Lax')
            return response
        else:
            msg = 'Invalid username or password.'
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
            Username: <input type="text" name="username" required/><br/>
            Password: <input type="password" name="password" required/><br/>
            <input type="submit" value="Login"/>
        </form>
        <p>{{msg}}</p>
        <a href="{{ url_for('index') }}">Back to Home</a>
    ''', msg=msg)

# Protected route
@app.route('/dashboard')
def dashboard():
    token = request.cookies.get('session_token')
    if token:
        user = get_user_by_session(token)
        if user:
            return render_template_string('''
                <h2>Dashboard</h2>
                <p>Welcome, {{username}}!</p>
                <a href="{{ url_for('logout') }}">Logout</a>
            ''', username=user['username'])
    return redirect(url_for('login'))

# Logout route
@app.route('/logout')
def logout():
    token = request.cookies.get('session_token')
    if token:
        delete_session(token)
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('session_token')
    return response

# ---------------- Run the App ----------------

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
