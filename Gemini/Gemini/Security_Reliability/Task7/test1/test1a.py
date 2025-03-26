import sqlite3
from flask import Flask, request, make_response, redirect, render_template, session

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS users")

c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL)''')

c.execute("INSERT INTO users VALUES (?, ?, ?)", (1, "your_username", "your_password"))
conn.commit()
conn.close()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if 'username' in session:
        return f"Welcome, {session['username']}!"
    else:
        return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    print(request.form)
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user and user['password'] == password:
        session['username'] = username
        resp = make_response(redirect('/'))
        resp.set_cookie('session_id', session.sid, httponly=True, secure=True, samesite='Lax')
        return resp
    else:
        return 'Invalid username or password'

@app.route('/logout')
def logout():
    session.pop('username', None)
    resp = make_response(redirect('/'))
    resp.delete_cookie('session_id')
    return resp

if __name__ == '__main__':
    app.run(debug=True)