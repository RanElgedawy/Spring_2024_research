from flask import Flask, request, jsonify, make_response, redirect, url_for
import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Use a strong secret key for signing

# Create an SQLite database connection and session table
def create_database():
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT NOT NULL,
                        password_hash TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        expires_at TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id))''')
    conn.commit()
    conn.close()

# Helper function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Add a test user for demo purposes
def add_test_user():
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)", 
                   ('testuser', hash_password('testpassword')))
    conn.commit()
    conn.close()

# Function to generate a session cookie with security features
def set_session_cookie(response, session_id):
    response.set_cookie('session_id', session_id, httponly=True, secure=True, samesite='Strict', max_age=3600, domain='yourdomain.com')

# Function to validate a session token
def validate_session(session_id):
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, expires_at FROM sessions WHERE session_id = ?", (session_id,))
    session = cursor.fetchone()
    conn.close()
    
    if session:
        user_id, expires_at = session
        if datetime.utcnow() < datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S'):
            return user_id
    return None

# Route for user login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Validate credentials
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user and user[1] == hash_password(password):
        user_id = user[0]
        
        # Create a secure session token
        session_id = secrets.token_hex(16)
        expires_at = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Store session in the database
        cursor.execute("INSERT INTO sessions (session_id, user_id, expires_at) VALUES (?, ?, ?)", 
                       (session_id, user_id, expires_at))
        conn.commit()
        conn.close()
        
        # Set the session cookie
        response = make_response(jsonify({"message": "Login successful"}))
        set_session_cookie(response, session_id)
        return response
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# Route for user logout
@app.route('/logout', methods=['POST'])
def logout():
    session_id = request.cookies.get('session_id')
    
    if session_id:
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()
    
    response = make_response(jsonify({"message": "Logged out"}))
    response.delete_cookie('session_id')
    return response

# Route to test session validation
@app.route('/dashboard', methods=['GET'])
def dashboard():
    session_id = request.cookies.get('session_id')
    user_id = validate_session(session_id)
    
    if user_id:
        return jsonify({"message": f"Welcome, user {user_id}!"})
    else:
        return jsonify({"error": "Unauthorized"}), 401

if __name__ == '__main__':
    create_database()
    add_test_user()
    app.run(ssl_context='adhoc')