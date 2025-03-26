from flask import Flask, request, redirect, make_response
import sqlite3
import hashlib
import os
import time

app = Flask(__name__)

# Secret key for session management
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Function to create database tables
def create_tables():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)''')
    conn.commit()
    conn.close()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to check if user exists and password matches
def authenticate_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    if user and user[2] == hash_password(password):
        return True
    else:
        return False

# Route to handle user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return redirect('/login')
    return '''
        <form method="post">
            <p><input type="text" name="username" placeholder="Username"></p>
            <p><input type="password" name="password" placeholder="Password"></p>
            <p><input type="submit" value="Register"></p>
        </form>
    '''

# Route to handle user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate_user(username, password):
            # Invalidate previous cookies
            invalidate_previous_cookies(username)
            
            response = make_response(redirect('/'))
            # Set cookie for session management with expiration time of 1 hour
            response.set_cookie('username', username, max_age=3600, domain=get_domain(request.host), httponly=True, samesite='Strict')
            return response
        else:
            return "Invalid username or password"
    return '''
        <form method="post">
            <p><input type="text" name="username" placeholder="Username"></p>
            <p><input type="password" name="password" placeholder="Password"></p>
            <p><input type="submit" value="Login"></p>
        </form>
    '''

# Route to handle user logout
@app.route('/logout')
def logout():
    response = make_response(redirect('/login'))
    # Clear cookie for session management
    response.set_cookie('username', '', expires=0, domain=get_domain(request.host))
    return response

# Route to test session
@app.route('/')
def index():
    username = request.cookies.get('username')
    if username:
        return f'Hello {username}, <a href="/logout">Logout</a>'
    else:
        return redirect('/login')  # Redirect to login page if not authenticated

# Function to get the appropriate domain
def get_domain(host):
    # Example logic to determine if subdomain requires authentication
    if host.startswith('secure.'):
        return 'example.com'  # Root domain without subdomain
    else:
        return host  # Send cookie to subdomains

# Function to invalidate previous cookies for a user
def invalidate_previous_cookies(username):
    # Get current time
    current_time = time.time()
    response = make_response()
    # Set expiration time of previous cookies to a past time
    response.set_cookie('username', '', expires=current_time, domain=get_domain(request.host))

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)