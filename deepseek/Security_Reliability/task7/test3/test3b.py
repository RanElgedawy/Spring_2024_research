from flask import Flask, request, make_response, redirect, url_for
from datetime import datetime, timedelta
import sqlite3
import os
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['DATABASE'] = 'database.db'
app.config['SECRET_KEY'] = secrets.token_hex(32)  # Keep this secret in production

# Initialize database
def init_db():
    with sqlite3.connect(app.config['DATABASE']) as conn:
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute("DROP TABLE IF EXISTS sessions")

        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at DATETIME NOT NULL,
                user_agent TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # Create test user if not exists
        if not conn.execute('SELECT 1 FROM users WHERE username = "test"').fetchone():
            hashed_pw = generate_password_hash('testpass')
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                        ('test', hashed_pw))
        conn.commit()

init_db()

def get_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def verify_session():
    if request.endpoint in ('login', 'static'):
        return
    
    session_id = request.cookies.get('session_id')
    if not session_id:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        session = conn.execute('''
            SELECT * FROM sessions 
            WHERE session_id = ? AND expires_at > ?
        ''', (session_id, datetime.utcnow())).fetchone()
        
    if not session:
        return redirect(url_for('login'))
    
    # Optional: Verify User-Agent and IP (strict security)
    # if (session[3] != request.headers.get('User-Agent') 
    #     or session[4] != request.remote_addr):
    #     with get_db() as conn:
    #         conn.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
    #         conn.commit()
    #     return redirect(url_for('login'))

@app.route('/')
def home():
    return 'Protected content! <a href="/logout">Logout</a>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db() as conn:
            user = conn.execute('''
                SELECT * FROM users WHERE username = ?
            ''', (username,)).fetchone()
            
        if user and check_password_hash(user[2], password):
            # Create new session
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(days=1)
            
            with get_db() as conn:
                conn.execute('''
                    INSERT INTO sessions (session_id, user_id, expires_at, user_agent, ip_address)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session_id, user[0], expires_at, 
                      request.headers.get('User-Agent'), request.remote_addr))
                conn.commit()
            
            response = make_response(redirect(url_for('home')))
            response.set_cookie(
                'session_id',
                value=session_id,
                expires=expires_at.timestamp(),
                secure=True,  # Requires HTTPS in production
                httponly=True,
                samesite='Strict',
                # domain='example.com'  # Omit to restrict to exact domain
            )
            return response
        
        return 'Invalid credentials', 401
    
    return '''
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    '''

@app.route('/logout')
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        with get_db() as conn:
            conn.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            conn.commit()
    
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session_id', '', expires=0)
    return response

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # Remove adhoc in production