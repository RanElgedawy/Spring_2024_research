from flask import Flask, request, make_response, redirect, url_for
import hashlib
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def validate_login(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and hashlib.sha256(password.encode()).hexdigest() == user['password']:
        return True
    return False

def set_session_cookie(response, user_id):
    response.set_cookie('session_id', str(user_id), domain=request.host, path='/')

def get_session_cookie(request):
    session_id = request.cookies.get('session_id')
    return session_id

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if validate_login(username, password):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id = cursor.fetchone()['id']
        conn.close()

        response = make_response(redirect(url_for('home')))
        set_session_cookie(response, user_id)
        return response
    else:
        # Handle login failure (e.g., display an error message)
        return "Invalid username or password"

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('session_id')
    return response

@app.route('/home')
def home():
    session_id = get_session_cookie(request)
    if session_id:
        # User is logged in, display protected content
        return "Welcome, logged-in user!"
    else:
        # User is not logged in, redirect to login page
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)