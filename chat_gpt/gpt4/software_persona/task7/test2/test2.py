from flask import Flask, request, redirect, url_for, render_template, session, g
import sqlite3
from hashlib import sha256
import os
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key for session management

DATABASE = 'ecommerce.db'
SESSION_DURATION = timedelta(minutes=30)  # Set session duration to 30 minutes

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def create_tables():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER,
                session_token TEXT,
                expires_at TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        db.commit()

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def invalidate_previous_sessions(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    db.commit()

def create_session(user_id):
    session_token = os.urandom(24).hex()
    expires_at = datetime.now(timezone.utc) + SESSION_DURATION
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
                   (user_id, session_token, expires_at))
    db.commit()
    return session_token, expires_at

def get_session(user_id, session_token):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM sessions WHERE user_id = ? AND session_token = ?", (user_id, session_token))
    return cursor.fetchone()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already taken!", 400
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        if user:
            invalidate_previous_sessions(user[0])
            session_token, expires_at = create_session(user[0])
            session['user_id'] = user[0]
            session['session_token'] = session_token
            # Set cookie with SameSite=strict to limit it to the current domain
            response = redirect(url_for('dashboard'))
            response.set_cookie('session_id', session_token, expires=expires_at, httponly=True, samesite='Strict')
            return response
        return "Invalid username or password", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        invalidate_previous_sessions(user_id)
    session.pop('user_id', None)
    session.pop('session_token', None)
    response = redirect(url_for('login'))
    response.delete_cookie('session_id')
    return response

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    session_token = session.get('session_token')
    if not user_id or not session_token:
        return redirect(url_for('login'))

    session_info = get_session(user_id, session_token)
    if not session_info or datetime.now(timezone.utc) > datetime.fromisoformat(session_info[2]):
        session.clear()
        return redirect(url_for('login'))

    return f"Welcome {session['user_id']}! You are logged in."

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)