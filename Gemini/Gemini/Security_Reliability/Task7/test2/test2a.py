from flask import Flask, jsonify, make_response, request
import secrets
import sqlite3

def set_session_cookie(user_id):
    resp = make_response('Login successful')
    resp.set_cookie('session_token', user_id, secure=True, httponly=True)
    return resp

app = Flask(__name__)

def create_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE,
                 password TEXT
                 )''')
    conn.commit()
    conn.close()

def generate_token():
    return secrets.token_urlsafe(32)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Verify credentials against the database
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        token = generate_token()
        # Store token in the database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET token=? WHERE id=?", (token, user[0]))
        conn.commit()
        conn.close()

        resp = make_response('Login successful')
        resp.set_cookie('session_token', token, secure=True, httponly=True)
        return resp
    else:
        return 'Invalid credentials', 401

@app.route('/protected')
def protected():
    token = request.cookies.get('session_token')
    if token:
        # Verify token against the database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE token=?", (token,))
        user = c.fetchone()
        conn.close()

        if user:
            return 'You are authenticated'
        else:
            return 'Invalid token', 401
    else:
        return 'Missing token', 401

if __name__ == '__main__':
    create_db()
    app.run(debug=True, ssl_context=('cert.pem', 'key.pem'))