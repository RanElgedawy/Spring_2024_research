from flask import Flask, request, redirect, make_response, render_template_string
from datetime import datetime, timedelta
import sqlite3
import os
import hashlib
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database initialization
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS sessions")

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  email TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (session_id TEXT PRIMARY KEY,
                  user_id INTEGER NOT NULL,
                  expires_at TEXT NOT NULL,  
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # Add test user if not exists
    try:
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                 ('testuser', hashlib.sha256('testpass'.encode()).hexdigest()))
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect('users.db')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_session(user_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
    
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(seconds=30)# timedelta(hours=1)
    
    # Store as ISO format string with 'T' separator
    conn.execute('INSERT INTO sessions VALUES (?, ?, ?)', 
                (session_id, user_id, expires_at.isoformat()))
    conn.commit()
    conn.close()
    
    return session_id, expires_at

def validate_session(session_id):
    if not session_id:
        return None
    
    conn = get_db_connection()
    try:
        session = conn.execute('SELECT * FROM sessions WHERE session_id = ?', 
                             (session_id,)).fetchone()
        if not session:
            return None

        # Parse ISO format with 'T' separator
        expires_at = datetime.fromisoformat(session[2])
        if datetime.utcnow() > expires_at:
            return None
        
        return session[1]  # Return user_id
    except Exception as e:
        print(f"Session validation error: {str(e)}")
        return None
    finally:
        conn.close()

@app.route('/')
def home():
    session_id = request.cookies.get('session_id')
    user_id = validate_session(session_id)
    
    if user_id:
        conn = get_db_connection()
        user = conn.execute('SELECT username FROM users WHERE id = ?', 
                          (user_id,)).fetchone()
        conn.close()
        return f'Welcome {user[0]}! <a href="/logout">Logout</a>'
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        conn = get_db_connection()
        user = conn.execute('SELECT id, password_hash FROM users WHERE username = ?', 
                          (username,)).fetchone()
        conn.close()
        
        if user and hash_password(password) == user[1]:
            session_id, expires_at = create_session(user[0])
            response = make_response(redirect('/'))
            response.set_cookie(
                'session_id',
                value=session_id,
                expires=expires_at,
                httponly=True,
                secure=False,
                samesite='Lax',
                path='/'
            )
            return response
        
        return 'Invalid credentials'
    
    return render_template_string('''
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p>Test user: testuser/testpass</p>
    ''')

@app.route('/logout')
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        conn = get_db_connection()
        conn.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()
    
    response = make_response(redirect('/login'))
    response.delete_cookie('session_id')
    return response

if __name__ == '__main__':
    app.run(debug=True)