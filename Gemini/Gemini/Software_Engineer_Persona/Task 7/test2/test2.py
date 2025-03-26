import os
import secrets
import sqlite3
import uuid
from flask import Flask, request, make_response, redirect, url_for, session, render_template
import datetime

app = Flask(__name__)

# Set secret key for session management
app.secret_key = secrets.token_hex(16)

# Database configuration
DB_NAME = "users.db"

def create_database_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create the `users` table if it doesn't exist
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            session_id TEXT
        )
    """)

    cursor.execute("INSERT INTO users (username, password) VALUES ('user1', 'password123')")
    cursor.execute("INSERT INTO users (username, password) VALUES ('user2', 'password456')")

    conn.commit()
    conn.close()

# Sample user data for testing
def populate_test_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO users (username, password) VALUES ('user1', 'password123')")
    cursor.execute("INSERT INTO users (username, password) VALUES ('user2', 'password456')")

    print(cursor.fetchall())
    conn.commit()
    conn.close()

def set_session_cookie(user_id, session_id, expiration_time=3600):
    """Sets a session cookie with the specified user ID, session ID, and expiration time."""
    expires = datetime.datetime.now() + datetime.timedelta(seconds=expiration_time)
    resp = make_response(redirect(url_for('home')))
    resp.set_cookie('user_id', str(user_id), expires=expires, domain=request.host, samesite='Lax')
    resp.set_cookie('session_id', session_id, expires=expires, domain=request.host, samesite='Lax')
    return resp

def create_session(user_id):
    """Creates a new session for the given user ID."""
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET session_id=? WHERE id=?", (session_id, user_id))
    conn.commit()
    conn.close()
    
    session['session_id'] = session_id
    session['user_id'] = user_id

    return session_id

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate user credentials against the database
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
            user_id = cursor.fetchone()
            conn.close()

            if user_id:
                # Set session cookie with expiration time
                session_id = create_session(user_id[0])
                return set_session_cookie(user_id[0], session_id, expiration_time=3600)
            else:
                return render_template('login.html', error='Invalid username or password')
        except Exception as e:
            # Handle database errors
            print(f"Database error: {e}")
            return render_template('login.html', error='An error occurred')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_id' in session and 'session_id' in session:
        user_id = session['user_id']
        session_id = session['session_id']
        # Retrieve user information from the database using user_id
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT session_id FROM users WHERE id=?", (user_id,))
            db_session_id = cursor.fetchone()
            conn.close()

            if db_session_id and db_session_id[0] == session_id:
                username = db_session_id[0]
                return render_template('home.html', username=username)
            else:
                return redirect(url_for('login'))
        except Exception as e:
            # Handle database errors
            print(f"Database error: {e}")
            return render_template('login.html', error='An error occurred')
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    create_database_tables()
    # Populate test data (optional)
    # populate_test_data()
    app.run(debug=True)