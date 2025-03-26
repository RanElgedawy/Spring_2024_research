import os
import sqlite3
import secrets
import datetime
from flask import Flask, request, redirect, url_for, g, make_response

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')  # Change in production!

# Database setup
def get_db():
    db = sqlite3.connect('sessions.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS sessions")

        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT NOT NULL UNIQUE,
                user_agent TEXT,
                expires_at DATETIME NOT NULL
            )
        ''')
        db.commit()

init_db()

# Security configuration
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,        # Requires HTTPS in production
    SESSION_COOKIE_SAMESITE='Strict',
    SESSION_COOKIE_NAME='__Secure-SID' # Secure cookie prefix
)

def create_session(user_id, user_agent):
    db = get_db()
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)
    
    db.execute('''
        INSERT INTO sessions (user_id, session_token, user_agent, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, session_token, user_agent, expires_at))
    db.commit()
    
    return session_token, expires_at

def validate_session(session_token):
    db = get_db()
    session = db.execute('''
        SELECT * FROM sessions 
        WHERE session_token = ? 
        AND expires_at > ?
    ''', (session_token, datetime.datetime.now())).fetchone()
    
    if session and session['user_agent'] == request.headers.get('User-Agent', ''):
        return session
    return None

@app.before_request
def authenticate_user():
    if request.endpoint in ['login', 'static', 'test_public']:
        return
    
    session_token = request.cookies.get('session_token')
    session = validate_session(session_token) if session_token else None
    
    if not session:
        return redirect(url_for('login'))
    
    g.user_id = session['user_id']

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # In real implementation: verify credentials against user database
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Dummy authentication - replace with real checks
        if username == 'test' and password == 'password':
            session_token, expires_at = create_session(
                user_id=1,  # Get real user ID from DB
                user_agent=request.headers.get('User-Agent', '')
            )
            
            response = redirect(url_for('dashboard'))
            response.set_cookie(
                'session_token',
                value=session_token,
                httponly=True,
                secure=True,
                samesite='Strict',
                expires=expires_at
            )
            return response
    
    return '''
        <form method="post">
            <input type="text" name="username" placeholder="Username">
            <input type="password" name="password" placeholder="Password">
            <button type="submit">Login</button>
        </form>
    '''

@app.route('/logout')
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        db = get_db()
        db.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
        db.commit()
    
    response = redirect(url_for('login'))
    response.set_cookie('session_token', '', expires=0)
    return response

@app.route('/dashboard')
def dashboard():
    return f'Welcome User {g.user_id}! <a href="/logout">Logout</a>'

@app.route('/test-public')
def test_public():
    return 'Public page - no authentication required'

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # Remove 'adhoc' in production
