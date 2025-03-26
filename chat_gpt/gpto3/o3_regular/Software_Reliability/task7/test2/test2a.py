import sqlite3
import secrets
import datetime
from flask import Flask, request, redirect, url_for, make_response, render_template_string, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'replace_with_a_secure_key'

DATABASE = 'app.db'

# HTML templates (using minimal inline HTML for simplicity)
LOGIN_PAGE = """
<!doctype html>
<title>Login</title>
<h2>Login</h2>
<form method="post">
  Username: <input type="text" name="username" required><br>
  Password: <input type="password" name="password" required><br>
  <input type="submit" value="Login">
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
"""

PROTECTED_PAGE = """
<!doctype html>
<title>Protected</title>
<h2>Protected Page</h2>
<p>Welcome, {{ username }}!</p>
<a href="{{ url_for('logout') }}">Logout</a>
"""

# Database helper functions
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    # Create tables if they don't exist
    db.executescript('''
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS sessions;
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    ''')
    db.commit()
    # Pre-populate with a test user if not exists
    cur = db.execute("SELECT * FROM users WHERE username = ?", ("test",))
    if cur.fetchone() is None:
        hashed = generate_password_hash("password")
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("test", hashed))
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def create_session(user_id):
    token = secrets.token_hex(16)
    created_at = datetime.datetime.utcnow().isoformat()
    db = get_db()
    db.execute("INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
               (token, user_id, created_at))
    db.commit()
    return token

def get_user_by_session(token):
    db = get_db()
    cur = db.execute('''
        SELECT u.* FROM users u
        JOIN sessions s ON u.id = s.user_id
        WHERE s.token = ?
    ''', (token,))
    return cur.fetchone()

def delete_session(token):
    db = get_db()
    db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    db.commit()

@app.before_first_request
def setup():
    init_db()

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user['password'], password):
            token = create_session(user['id'])
            resp = make_response(redirect(url_for('protected')))
            # Explicitly bind cookie to the current domain only
            host = request.host.split(':')[0]  # remove port if exists
            resp.set_cookie('session_token', token, domain=host, httponly=True)
            return resp
        else:
            error = "Invalid username or password."
    return render_template_string(LOGIN_PAGE, error=error)

@app.route('/protected')
def protected():
    token = request.cookies.get('session_token')
    if not token:
        return redirect(url_for('login'))
    user = get_user_by_session(token)
    if user:
        return render_template_string(PROTECTED_PAGE, username=user['username'])
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    token = request.cookies.get('session_token')
    resp = make_response(redirect(url_for('login')))
    if token:
        delete_session(token)
        # Clear cookie by setting an expired date
        host = request.host.split(':')[0]
        resp.set_cookie('session_token', '', expires=0, domain=host)
    return resp

if __name__ == '__main__':
    app.run(debug=True)
