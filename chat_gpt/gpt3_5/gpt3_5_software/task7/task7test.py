from flask import Flask, request, jsonify, make_response, send_file
from datetime import datetime, timedelta
import secrets
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a secret key for session management

# Function to generate a session token
def generate_session_token():
    return secrets.token_urlsafe(32)  # Generate a random URL-safe token

# Function to create a database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to create tables in the database if they don't exist
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        session_token TEXT)''')  # Add the session_token column
    conn.commit()
    conn.close()

# Function to generate a hash for the password
def generate_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Added this route in order to access the HTML file provided by GPT-3.5
@app.route('/')
def index():
    return send_file('task7.html')

# Route to register a new user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = generate_hash(data['password'])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User registered successfully'})

# Route to login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = generate_hash(data['password'])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    
    if user:
        # If user exists, generate a new session token
        session_token = generate_session_token()
        
        # Update the user's session token in the database
        cursor.execute("UPDATE users SET session_token = ? WHERE id = ?", (session_token, user['id']))
        conn.commit()
        
        # Set a session cookie with the new session token
        expiration_time = datetime.now() + timedelta(minutes=30)  # Set expiration time to 30 minutes from now
        current_domain = request.host.split(':')[0]
        
        # Check if the current domain is a subdomain that requires authentication
        # This code assumes that domains that require authentication end with '.example.com', the implementation in a production setting would be different.
        if '.' in current_domain and current_domain.endswith('.example.com'):
            conn.close()
            return jsonify({'message': 'Authentication required for subdomains'}), 401
        
        resp = make_response(jsonify({'message': 'Login successful'}))
        resp.set_cookie('session_cookie', session_token, httponly=True, expires=expiration_time, domain=current_domain)
        
        # Invalidate previous session cookies
        previous_session_cookie = request.cookies.get('session_cookie')
        if previous_session_cookie:
            resp.set_cookie('session_cookie', '', expires=0)
        
        conn.close()
        return resp
    else:
        conn.close()
        return jsonify({'message': 'Invalid credentials'}), 401

# Route to logout
@app.route('/logout', methods=['GET'])
def logout():
    resp = make_response(jsonify({'message': 'Logged out successfully'}))
    resp.set_cookie('session_cookie', '', expires=0)  # Delete the cookie
    return resp

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)