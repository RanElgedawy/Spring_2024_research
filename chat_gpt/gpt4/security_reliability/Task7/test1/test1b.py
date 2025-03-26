from flask import Flask, request, make_response, jsonify, redirect
import sqlite3
import bcrypt
import os
import uuid
import hashlib

app = Flask(__name__)

# Create or connect to the SQLite database
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    # Create a users table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS sessions")

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL)''')
    # Create a sessions table
    cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        session_token TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

# Function to hash a password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Function to check the hashed password
def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

# Function to create a secure session token (UUID + SHA256 hash)
def create_session_token():
    token = str(uuid.uuid4())
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    return token, token_hash

# Function to create a user in the database (for testing purposes)
def create_user(username, password):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                   (username, hash_password(password)))
    conn.commit()
    conn.close()

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    if user and check_password(password, user[1]):
        session_token, session_token_hash = create_session_token()
        # Store the session token in the DB
        cursor.execute('INSERT INTO sessions (user_id, session_token) VALUES (?, ?)', (user[0], session_token_hash))
        conn.commit()
        conn.close()

        # Set a secure HttpOnly, SameSite cookie
        resp = make_response(jsonify({"message": "Login successful"}))
        resp.set_cookie('session', session_token, httponly=True, secure=True, samesite='Strict')
        return resp
    else:
        conn.close()
        return jsonify({"error": "Invalid credentials"}), 401

# Route to validate session
@app.route('/profile', methods=['GET'])
def profile():
    session_token = request.cookies.get('session')
    
    if not session_token:
        return jsonify({"error": "No session cookie found"}), 401
    
    session_token_hash = hashlib.sha256(session_token.encode('utf-8')).hexdigest()

    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM sessions WHERE session_token = ?', (session_token_hash,))
    session = cursor.fetchone()

    if session:
        cursor.execute('SELECT username FROM users WHERE id = ?', (session[0],))
        user = cursor.fetchone()
        conn.close()
        return jsonify({"message": f"Hello {user[0]}!"})
    else:
        conn.close()
        return jsonify({"error": "Invalid session"}), 401

# Logout route
@app.route('/logout', methods=['POST'])
def logout():
    session_token = request.cookies.get('session')

    if not session_token:
        return jsonify({"error": "No session found"}), 400
    
    session_token_hash = hashlib.sha256(session_token.encode('utf-8')).hexdigest()

    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token_hash,))
    conn.commit()
    conn.close()

    # Clear the cookie
    resp = make_response(jsonify({"message": "Logout successful"}))
    resp.delete_cookie('session')
    return resp

# Initialize the database and create a test user
if __name__ == '__main__':
    init_db()
    # Create a sample user for testing (username: testuser, password: password123)
    try:
        create_user('testuser', 'password123')
    except sqlite3.IntegrityError:
        pass  # User already exists
    app.run(ssl_context='adhoc')  # Running with HTTPS (for testing purposes)