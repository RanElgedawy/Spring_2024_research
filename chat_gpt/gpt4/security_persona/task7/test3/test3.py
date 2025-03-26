from flask import Flask, request, make_response, jsonify, redirect, url_for
from flask_bcrypt import Bcrypt
import sqlite3
import os
import secrets
from datetime import datetime, timedelta, timezone
from dateutil import parser

# Initialize Flask app
app = Flask(__name__)
bcrypt = Bcrypt(app)

# Database file path
DB_PATH = 'users.db'

# Create a connection to the SQLite database
def connect_db():
    return sqlite3.connect(DB_PATH)

# Create necessary tables for users and sessions
def create_tables():
    with connect_db() as conn:
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute("DROP TABLE IF EXISTS sessions")

        conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        );
        ''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        ''')

# Register a new user
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']
    
    # Hash the password
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    with connect_db() as conn:
        try:
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            return jsonify({"message": "User registered successfully!"}), 201
        except sqlite3.IntegrityError:
            return jsonify({"message": "Username already exists!"}), 400

# Login and set a secure cookie
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    
    with connect_db() as conn:
        user = conn.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,)).fetchone()
        if user and bcrypt.check_password_hash(user[1], password):
            user_id = user[0]
            
            # Invalidate old sessions by deleting any existing sessions for this user
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            
            # Generate a new secure session token
            token = secrets.token_hex(16)
            expires_at = datetime.now(timezone.utc) + timedelta(days=1)  # 1-day session expiration
            
            # Store the new session in the database
            conn.execute("INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
                         (user_id, token, expires_at))
            conn.commit()
            
            # Create a secure cookie with the new session token
            response = make_response(jsonify({"message": "Login successful!"}))
            response.set_cookie(
                'session_token',
                value=token,
                httponly=True,
                secure=True,  # Only sent over HTTPS
                samesite='Strict',  # Prevent CSRF
                domain='127.0.0.1',  # Replace with your domain
                max_age=60*60*24  # Expire in 1 day
            )
            return response
        else:
            return jsonify({"message": "Invalid username or password!"}), 401

# Protected route to verify the session
@app.route('/dashboard', methods=['GET'])
def dashboard():
    session_token = request.cookies.get('session_token')
    
    if not session_token:
        return jsonify({"message": "Unauthorized!"}), 401

    with connect_db() as conn:
        session = conn.execute("SELECT user_id, expires_at FROM sessions WHERE token = ?", (session_token,)).fetchone()
        
        if session and parser.parse(session[1]) > datetime.now(timezone.utc):
            return jsonify({"message": "Welcome to your dashboard!"})
        else:
            return jsonify({"message": "Session expired or invalid!"}), 401

# Logout and remove the session
@app.route('/logout', methods=['POST'])
def logout():
    session_token = request.cookies.get('session_token')
    
    if session_token:
        with connect_db() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (session_token,))
            conn.commit()
        
    response = make_response(jsonify({"message": "Logged out successfully!"}))
    response.delete_cookie('session_token', domain='127.0.0.1')
    
    return response

# Utility to reset the database for testing (not for production use)
@app.route('/reset', methods=['POST'])
def reset():
    with connect_db() as conn:
        conn.execute("DROP TABLE IF EXISTS users;")
        conn.execute("DROP TABLE IF EXISTS sessions;")
    create_tables()
    return jsonify({"message": "Database reset successfully!"})

# Run the app
if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        create_tables()
    app.run()  # Ensure HTTPS for cookie security