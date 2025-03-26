from flask import Flask, request, redirect, url_for, session, render_template_string, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

# Configuration
DATABASE = 'user_sessions.db'
SECRET_KEY = 'supersecretkey'  # Change this to a random value
COOKIE_NAME = 'session_id'
SESSION_TIMEOUT = 1  # Session timeout in minutes
DOMAIN = 'example.com'  # Replace with your actual domain

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = app.config['SECRET_KEY']

# Helper functions
def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with connect_db() as db:
        db.cursor().executescript('''      
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def is_session_valid(session_id):
    result = g.db.execute('''
        SELECT user_id, expires_at 
        FROM sessions 
        WHERE session_id = ?''', (session_id,)).fetchone()
    
    if result:
        user_id, expires_at = result
        if datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S') > datetime.now():
            return user_id
        else:
            g.db.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            g.db.commit()
    return None

# Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        try:
            g.db.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                         (username, hashed_password))
            g.db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists"
    
    return render_template_string('''
        <form method="post">
            <p>Username: <input type=text name=username>
            <p>Password: <input type=password name=password>
            <p><input type=submit value=Register>
        </form>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = g.db.execute('SELECT id, password FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user[1], password):
            # Invalidate any existing sessions for this user
            g.db.execute('DELETE FROM sessions WHERE user_id = ?', (user[0],))
            g.db.commit()
            
            # Create a new session
            session_id = generate_password_hash(username + app.secret_key)
            session[COOKIE_NAME] = session_id
            
            expires_at = datetime.now() + timedelta(minutes=SESSION_TIMEOUT)
            g.db.execute('INSERT INTO sessions (user_id, session_id, expires_at) VALUES (?, ?, ?)',
                         (user[0], session_id, expires_at.strftime('%Y-%m-%d %H:%M:%S')))
            g.db.commit()
            
            # Set the cookie to expire at the same time as the session
            session.permanent = True
            app.permanent_session_lifetime = timedelta(minutes=SESSION_TIMEOUT)
            
            # Restrict the cookie to the specified domain only
            session_cookie = session[COOKIE_NAME]
            response = redirect(url_for('dashboard'))
            response.set_cookie(COOKIE_NAME, session_cookie, max_age=SESSION_TIMEOUT*60, domain=DOMAIN)
            
            return response
        return "Invalid credentials"
    
    return render_template_string('''
        <form method="post">
            <p>Username: <input type=text name=username>
            <p>Password: <input type=password name=password>
            <p><input type=submit value=Login>
        </form>
    ''')

@app.route('/dashboard')
def dashboard():
    session_id = session.get(COOKIE_NAME)
    if session_id:
        user_id = is_session_valid(session_id)
        if user_id:
            return f"Welcome, user {user_id}!"
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session_id = session.pop(COOKIE_NAME, None)
    if session_id:
        g.db.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        g.db.commit()
    return redirect(url_for('login'))

# Database initialization
with app.app_context():
    init_db()

# Run the app
if __name__ == '__main__':
    app.run(debug=True)