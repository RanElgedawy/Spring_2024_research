from flask import Flask, request, make_response, redirect, url_for, render_template, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for signing sessions
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # Enable this for production (HTTPS)
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'

# Database setup
db_config = {
    'user': 'your_db_user',
    'password': 'your_db_password',
    'host': 'localhost',
    'database': 'your_db_name'
}

def create_user_table():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS sessions")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_token VARCHAR(255) PRIMARY KEY,
            user_id INT NOT NULL,
            expiry DATETIME NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    ''')
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, password_hash))
        conn.commit()
        cursor.close()
        conn.close()
        return 'User registered!'
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session_token = str(uuid.uuid4())
            expiry = datetime.utcnow() + timedelta(hours=1)
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO sessions (session_token, user_id, expiry) VALUES (%s, %s, %s)',
                           (session_token, user[0], expiry))
            conn.commit()
            cursor.close()
            conn.close()

            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie('session_token', session_token, httponly=True, secure=True, samesite='Strict')
            return response
        return 'Invalid credentials', 401
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return redirect(url_for('login'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM sessions WHERE session_token = %s AND expiry > %s', 
                   (session_token, datetime.utcnow()))
    session_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not session_data:
        return redirect(url_for('login'))
    
    return f'Welcome to your dashboard, user {session_data[0]}!'

@app.route('/logout')
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE session_token = %s', (session_token,))
        conn.commit()
        cursor.close()
        conn.close()

    response = make_response(redirect(url_for('login')))
    response.set_cookie('session_token', '', expires=0)  # Invalidate the cookie
    return response

if __name__ == '__main__':
    create_user_table()
    app.run(debug=True)