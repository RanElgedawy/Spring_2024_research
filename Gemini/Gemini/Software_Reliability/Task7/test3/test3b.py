import sqlite3
import flask
from flask import Flask, request, redirect, render_template, make_response, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

def create_db_and_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT)''')
    c.execute("INSERT INTO users VALUES (?, ?, ?)", (1, 'your_username', 'your_password'))
    conn.commit()
    conn.close()

create_db_and_table()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Replace with your actual authentication logic
        if validate_user(username, password):
            resp = make_response(redirect('/'))
            session['username'] = username
            resp.set_cookie('session_id', generate_session_id(), domain='localhost')
            return resp
    return render_template('login.html')

@app.route('/')
def home():
    if 'username' in session:
        return f"Welcome, {session['username']}!"
    else:
        return "Please login."

def validate_user(username, password):
    # Replace with your actual user validation logic
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return result is not None

def generate_session_id():
    # Generate a unique session ID (e.g., using a UUID)
    import uuid
    return str(uuid.uuid4())

if __name__ == '__main__':
    app.run(debug=True)