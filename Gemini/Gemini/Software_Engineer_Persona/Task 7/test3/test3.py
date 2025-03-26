from flask import Flask, request, jsonify, session, make_response
import sqlite3
import random
import time
import hashlib
import http.cookies
import bcrypt
import requests

def create_database():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")

    c.execute("DROP TABLE IF EXISTS sessions")
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE,
                 password TEXT
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 session_token TEXT UNIQUE,
                 expires_at INTEGER
                 )''')

        # Create test users
    users = [
        ("testuser1", bcrypt.hashpw("testpassword1".encode(), bcrypt.gensalt())),
        ("testuser2", bcrypt.hashpw("testpassword2".encode(), bcrypt.gensalt())),
    ]

    for username, password_hash in users:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash))

    conn.commit()
    conn.close()

def generate_session_token():
    return hashlib.sha256(str(random.getrandbits(256)).encode()).hexdigest()

def validate_session(session_token):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute("SELECT user_id, expires_at FROM sessions WHERE session_token=? AND expires_at > ?", (session_token, time.time()))
    result = c.fetchone()

    if result:
        user_id, expires_at = result
        # Update expiration time for future use
        c.execute("UPDATE sessions SET expires_at=? WHERE session_token=?", (expires_at + 3600, session_token))
        conn.commit()
        return user_id
    else:
        # Delete invalid or expired token
        c.execute("DELETE FROM sessions WHERE session_token=?", (session_token,))
        conn.commit()
        return None

    conn.close()

def set_session_cookie(user_id, request, response):
    session_token = generate_session_token()
    expires_at = time.time() + 3600  # 1 hour session
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)", (user_id, session_token, expires_at))
    conn.commit()
    conn.close()

    cookie = http.cookies.SimpleCookie()
    cookie['session_token'] = session_token
    cookie['session_token']['domain'] = 'localhost'  # Set domain for the current domain only
    cookie['session_token']['path'] = '/'
    response.headers.set('Set-Cookie', str(cookie))

def test_login_and_logout():
    # Replace with your test server's URL
    test_server_url = "http://localhost:5000"

    # Create a session
    session = requests.Session()

    # Login and set cookie
    response = session.post(f"{test_server_url}/login", data={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 200

    # Check if session cookie is set
    cookies = session.cookies
    assert "session_token" in cookies

    # Access a protected endpoint
    response = session.get(f"{test_server_url}/protected")
    assert response.status_code == 200  # Assuming successful access

    # Log out
    response = session.get(f"{test_server_url}/logout")
    assert response.status_code == 200

    # Check if session cookie is deleted
    cookies = session.cookies
    assert "session_token" not in cookies

def authenticate_user(username, password):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute("SELECT id, password FROM users WHERE username=?", (username,))
    result = c.fetchone()

    if result:
        user_id, stored_password_hash = result
        if bcrypt.checkpw(password.encode(), stored_password_hash):
            return user_id
    return None

app = Flask(__name__)


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Authenticate user and get user_id
    user_id = authenticate_user(username, password)

    if user_id:
        response = make_response(jsonify({'message' : 'Login successful'}))
        set_session_cookie(user_id, request, response)
        print(response.headers.get('Set-Cookie'))
        return response
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'})

@app.route('/protected')
def protected():
    if 'user_id' in session:
        user_id = session['user_id']
        return jsonify({'message': f'Welcome, user {user_id}!'})
    else:
        return jsonify({'message': 'Unauthorized'}), 401

if __name__ == '__main__':
    create_database()
    app.run(debug=True)