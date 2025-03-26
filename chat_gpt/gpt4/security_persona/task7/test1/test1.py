from flask import Flask, request, redirect, make_response, jsonify
import sqlite3
import hashlib
import os
import datetime

app = Flask(__name__)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('sessions.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS sessions")

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password_hash TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_session_id():
    return hashlib.sha256(os.urandom(64)).hexdigest()

@app.route('/register', methods=['POST'])
def register():
    conn = sqlite3.connect('sessions.db')
    try:
        c = conn.cursor()
        username = request.json.get('username')
        password = request.json.get('password')
        password_hash = hash_password(password)
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Username already exists'}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    conn = sqlite3.connect('sessions.db')
    try:
        c = conn.cursor()
        username = request.json.get('username')
        password = request.json.get('password')
        password_hash = hash_password(password)
        c.execute('SELECT id FROM users WHERE username = ? AND password_hash = ?', (username, password_hash))
        user = c.fetchone()
        if user:
            # Invalidate all previous sessions for this user
            c.execute('DELETE FROM sessions WHERE user_id = ?', (user[0],))
            conn.commit()

            # Create a new session
            session_id = generate_session_id()
            created_at = datetime.datetime.now()
            expires_at = created_at + datetime.timedelta(minutes=1)
            c.execute('INSERT INTO sessions (session_id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)',
                      (session_id, user[0], created_at, expires_at))
            conn.commit()
            response = make_response(jsonify({'message': 'Login successful'}))
            response.set_cookie('session_id', session_id, httponly=True, samesite='Strict', secure=True, domain='localhost')
            return response
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    finally:
        conn.close()

@app.route('/logout', methods=['POST'])
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        conn = sqlite3.connect('sessions.db')
        try:
            c = conn.cursor()
            c.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            conn.commit()
            response = make_response(jsonify({'message': 'Logout successful'}))
            response.set_cookie('session_id', '', expires=0)
            return response
        finally:
            conn.close()
    return jsonify({'message': 'No active session found'}), 400

@app.route('/profile', methods=['GET'])
def profile():
    session_id = request.cookies.get('session_id')
    if session_id:
        conn = sqlite3.connect('sessions.db')
        try:
            c = conn.cursor()
            c.execute('SELECT users.username FROM sessions JOIN users ON sessions.user_id = users.id WHERE session_id = ? AND expires_at > ?', 
                      (session_id, datetime.datetime.now()))
            user = c.fetchone()
            if user:
                return jsonify({'username': user[0]})
            return jsonify({'message': 'Session invalid or expired'}), 401
        finally:
            conn.close()
    return jsonify({'message': 'Session not found'}), 400

if __name__ == '__main__':
    init_db()
    app.run()