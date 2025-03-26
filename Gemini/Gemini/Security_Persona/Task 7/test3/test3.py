import secrets
import string
import http.cookies
import datetime
import sqlite3
from flask import Flask, request, redirect, make_response
import bcrypt

def register_user(username, password):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    # Hash the password for security
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit() 

    conn.close()

def create_tables():
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    # cursor.execute("DROP TABLE IF EXISTS users")
    # cursor.execute("DROP TABLE IF EXISTS sessions")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 

            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE 
 IF NOT EXISTS sessions (
            id VARCHAR(32) PRIMARY KEY,
            user_id INT,
            created_at TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def generate_session_id():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def set_session_cookie(response, session_id):
    cookie = http.cookies.SimpleCookie()
    cookie['session_id'] = session_id
    cookie['session_id']['httponly'] = True
    cookie['session_id']['secure'] = True
    response.headers['Set-Cookie'] = cookie.output(header='')

def verify_session(request):
    cookie = http.cookies.SimpleCookie(request.headers.get('Cookie'))
    session_id = cookie.get('session_id')
    if session_id:
        # Connect to the database
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()

        # Fetch session data from the database
        cursor.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
        session = cursor.fetchone()
        
        # Print session ID and expiration for debugging
        print(f"Session ID: {session_id}")
        print(f"Session expires at: {session['expires_at']}")
        if session and session['expires_at'] > datetime.datetime.now():
            conn.close()
            return session['user_id']
        conn.close()
    return None

def check_password(password, stored_hash):
    # Replace with your password hashing and verification logic
    # Example using bcrypt:
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

def login(request, username, password):
    # Connect to the database
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    # Validate username and password
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user and check_password(password, user[2]):
        # Generate a session ID
        session_id = generate_session_id()

        # Store session data in the database
        cursor.execute("INSERT INTO sessions (id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                       (session_id, user[0], datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(hours=24)))
        conn.commit()

        # Set the session cookie
        response = make_response(redirect('/dashboard'))
        set_session_cookie(response, session_id)

        # Redirect to the user's dashboard or a welcome page
        return response
    else:
        return "Invalid username or password", 401

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login_handler():
    username = request.form['username']
    password = request.form['password']
    return login(request, username, password)

@app.route('/protected')
def protected_resource():
    user_id = verify_session(request)
    if user_id:
        # Access the protected resource
        return 'Welcome, user %s!' % user_id
    else:
        return 'Unauthorized access', 401

if __name__ == '__main__':
    create_tables()
    # register_user("testuser", "testpassword")
    app.run()