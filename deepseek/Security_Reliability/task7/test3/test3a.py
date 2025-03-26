from flask import Flask, request, redirect, url_for, make_response, abort
import sqlite3
from datetime import datetime, timedelta
import secrets
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS sessions")

        # Create users table with test account
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at DATETIME NOT NULL,
                ip_hash TEXT NOT NULL,
                user_agent_hash TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create test user if not exists
        cursor.execute('SELECT 1 FROM users WHERE username = "test"')
        if not cursor.fetchone():
            password_hash = generate_password_hash('test')
            cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                         ('test', password_hash))
        
        db.commit()

init_db()

def generate_session_id():
    return secrets.token_urlsafe(32)

def hash_data(data):
    return hashlib.sha256(data.encode()).hexdigest()

def create_session(user_id, ip, user_agent):
    session_id = generate_session_id()
    expires_at = datetime.now() + timedelta(hours=1)
    db = get_db()
    db.execute('''
        INSERT INTO sessions (session_id, user_id, expires_at, ip_hash, user_agent_hash)
        VALUES (?, ?, ?, ?, ?)
    ''', (session_id, user_id, expires_at, hash_data(ip), hash_data(user_agent)))
    db.commit()
    return session_id

def validate_session(session_id, ip, user_agent):
    db = get_db()
    session = db.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,)).fetchone()
    
    if not session:
        return False
    
    if datetime.now() > datetime.fromisoformat(session['expires_at']):
        db.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        db.commit()
        return False
    
    if (hash_data(ip) != session['ip_hash'] or 
        hash_data(user_agent) != session['user_agent_hash']):
        db.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        db.commit()
        return False
    
    # Renew session expiration
    new_expires = datetime.now() + timedelta(hours=1)
    db.execute('UPDATE sessions SET expires_at = ? WHERE session_id = ?', 
              (new_expires, session_id))
    db.commit()
    return True

def delete_session(session_id):
    db = get_db()
    db.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
    db.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_db().execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            session_id = create_session(user['id'], request.remote_addr, 
                                      request.headers.get('User-Agent'))
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie(
                'session_id',
                session_id,
                httponly=True,
                secure=True,  # Set to False in development without HTTPS
                samesite='Strict',
                max_age=3600
            )
            return response
        abort(401, 'Invalid credentials')
    
    return '''
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    '''

@app.route('/dashboard')
def dashboard():
    session_id = request.cookies.get('session_id')
    if not session_id or not validate_session(session_id, request.remote_addr, 
                                           request.headers.get('User-Agent')):
        return redirect(url_for('login'))
    return '''
        <h1>Dashboard</h1>
        <p>Logged in successfully!</p>
        <a href="/logout">Logout</a>
    '''

@app.route('/logout')
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        delete_session(session_id)
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session_id', '', expires=0)
    return response

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # Remove in production if using reverse proxy with HTTPS