from flask import Flask, request, make_response, redirect, url_for
import sqlite3
import secrets
import datetime

def create_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE,
                 password TEXT,
                 session_token TEXT
                 )''')
    
    users = [
        ("user1", "password1"),
        ("user2", "password2"),
        ("user3", "password3")
    ]

    for username, password in users:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

app = Flask(__name__)

def set_cookie(response, username):
    token = secrets.token_urlsafe(32)
    # Set expiration time (e.g., 1 hour)
    expires = datetime.datetime.now() + datetime.timedelta(days=30)

    # Invalidate previous cookies for the same user
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET session_token = ? WHERE username = ?", (token, username))
    conn.commit()
    conn.close()

    response.set_cookie('session_token', token, expires=expires, secure=True, domain=request.host)
    return response

def get_user(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
  # This might return None if user not found
    conn.close()
    return user

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')  # Use request.form for POST data
    password = request.form.get('password')

    user = get_user(username)
    if user:  # Check if user exists before password comparison
        if user[2] == password:  # Access user[2] only if user is not None
            response = make_response(redirect('/dashboard'))
            return set_cookie(response, username)
        else:
            return "Invalid password"
    else:
        return "Invalid username"

@app.route('/dashboard')
def dashboard():
    session_token = request.cookies.get('session_token')
    print(f"Session token: {session_token}")
    if session_token:
        # Validate token against database or other storage
        # ...
        return "Welcome to the dashboard!"
    else:
        return redirect('/login')

if __name__ == '__main__':
    create_database()
    app.run(debug=True)