from flask import Flask, request, redirect, url_for, render_template, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'users.db'
COOKIE_NAME = 'session_id'

# Helper function to create database and users table
def init_db():
    if not os.path.exists(DATABASE):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute('''CREATE TABLE users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT UNIQUE NOT NULL,
                                password TEXT NOT NULL
                              )''')
            # Insert a sample user for testing
            cursor.execute('''INSERT INTO users (username, password)
                              VALUES (?, ?)''', ('testuser', generate_password_hash('password123')))
            conn.commit()

# Helper function to get a user from the database
def get_user(username):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cursor.fetchone()

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)

        if user and check_password_hash(user[2], password):
            # Create a session cookie for the user
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie(COOKIE_NAME, username, httponly=True, samesite='Lax')
            return response
        else:
            return 'Invalid credentials', 401

    return '''
        <form method="post">
            <p><input type="text" name="username" placeholder="Username">
            <p><input type="password" name="password" placeholder="Password">
            <p><input type="submit" value="Login">
        </form>
    '''

# Route for the dashboard, accessible only if logged in
@app.route('/dashboard')
def dashboard():
    username = request.cookies.get(COOKIE_NAME)
    if not username:
        return redirect(url_for('login'))
    
    user = get_user(username)
    if not user:
        return redirect(url_for('login'))

    return f'Welcome {username}! You are logged in.'

# Route for logging out
@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.set_cookie(COOKIE_NAME, '', expires=0)
    return response

# Initialize the database before the first request
@app.before_first_request
def initialize():
    init_db()

# Main function to run the app
if __name__ == '__main__':
    app.run(debug=True)