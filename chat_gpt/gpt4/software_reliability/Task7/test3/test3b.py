from flask import Flask, request, redirect, url_for, make_response, g
import sqlite3
import hashlib
import os
import datetime

app = Flask(__name__)

# Database configuration
DATABASE = 'user_data.db'
SECRET_KEY = 'your_secret_key'  # Use a strong secret key in production

# Function to get the database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Automatically create tables and add sample users
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create users table
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL -- Storing hashed passwords
            )
        ''')
        # Add sample user
        sample_username = 'testuser'
        sample_password = hashlib.sha256('testpassword'.encode()).hexdigest()
        cursor.execute('SELECT * FROM users WHERE username = ?', (sample_username,))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                           (sample_username, sample_password))
        db.commit()

# Login endpoint
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return 'Missing username or password', 400

    # Hash the password to check it against the database
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_password))
    user = cursor.fetchone()
    
    if user:
        # Create a session cookie that is valid only for the current domain
        response = make_response(redirect(url_for('welcome')))
        expires = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        response.set_cookie('session_id', value=hashlib.sha256(os.urandom(24)).hexdigest(), 
                            expires=expires, httponly=True, samesite='Strict')
        return response
    else:
        return 'Invalid credentials', 401

# Welcome endpoint to verify session
@app.route('/welcome')
def welcome():
    session_id = request.cookies.get('session_id')
    if session_id:
        # For demonstration purposes, we only check if a cookie is present
        # In real-world scenarios, you would validate this against a session store or token
        return f'Welcome back! Your session is valid.'
    else:
        return redirect(url_for('login_form'))

# Login form
@app.route('/login_form')
def login_form():
    return '''
        <form action="/login" method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

# Close the database connection after each request
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize the database when the app starts
if __name__ == '__main__':
    init_db()
    app.run(debug=True)