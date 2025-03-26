from flask import Flask, request, redirect, url_for, render_template_string, make_response
import sqlite3
import os
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
DATABASE = 'app.db'
SESSION_DURATION = timedelta(days=1)  # Sessions valid for 1 day

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        # Create a users table for testing purposes (if it doesn't already exist).
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
        ''')
        # Create a test user if one doesn't exist.
        user = conn.execute("SELECT * FROM users WHERE username = ?", ('test',)).fetchone()
        if not user:
            password_hash = generate_password_hash("password")
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ('test', password_hash))
            conn.commit()

        # Create sessions table.
        conn.execute("DROP TABLE IF EXISTS sessions")

        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        ''')
        conn.commit()

def create_session(user_id):
    token = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    expires_at = now + SESSION_DURATION
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, now, expires_at)
        )
        conn.commit()
    return token

def get_user_from_session(token):
    now = datetime.utcnow()
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT s.user_id, u.username, s.expires_at FROM sessions s JOIN users u ON s.user_id = u.id WHERE s.token = ?",
            (token,)
        ).fetchone()
        if row:
            # Parse the stored expiration time.
            expires_at = datetime.strptime(row['expires_at'], "%Y-%m-%d %H:%M:%S.%f")
            if now < expires_at:
                return {'id': row['user_id'], 'username': row['username']}
            else:
                # Session expired; remove it.
                conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
    return None

def delete_session(token):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if user and check_password_hash(user['password_hash'], password):
                token = create_session(user['id'])
                response = make_response(redirect(url_for('dashboard')))
                # Set the session cookie with secure flags.
                response.set_cookie('session', token, httponly=True, secure=True, samesite='Strict')
                return response
            else:
                error = 'Invalid username or password'
    # Simple login form. For testing, use: username "test" and password "password".
    return render_template_string('''
        <h2>Login</h2>
        {% if error %}
          <p style="color: red;">{{ error }}</p>
        {% endif %}
        <form method="post">
          Username: <input type="text" name="username" required><br>
          Password: <input type="password" name="password" required><br>
          <button type="submit">Login</button>
        </form>
    ''', error=error)

@app.route('/dashboard')
def dashboard():
    token = request.cookies.get('session')
    if token:
        user = get_user_from_session(token)
        if user:
            return f"Hello, {user['username']}! Welcome to your dashboard."
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    token = request.cookies.get('session')
    if token:
        delete_session(token)
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)
    return response

if __name__ == '__main__':
    init_db()
    # For local testing, run in debug mode on localhost.
    # In production, ensure your app runs under HTTPS.
    app.run(debug=True)
