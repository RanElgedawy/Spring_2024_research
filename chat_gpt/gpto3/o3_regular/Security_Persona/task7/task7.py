import sqlite3, secrets, datetime, os
from flask import Flask, request, redirect, url_for, render_template_string, make_response, g
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'app.db'
app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)  # Used for session signing

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    # Create sessions table for managing login sessions
    db.execute("DROP TABLE IF EXISTS sessions")
    db.execute("DROP TABLE IF EXISTS users")

    db.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER,
            expires TIMESTAMP
        )
    ''')
    # Create users table (for testing/demo purposes)
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    db.commit()

def create_sample_user():
    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE username = ?", ("testuser",))
    user = cur.fetchone()
    if user is None:
        hashed_password = generate_password_hash("testpass")
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("testuser", hashed_password))
        db.commit()

# Combined setup: initialize the DB and create a sample user
def setup():
    init_db()
    create_sample_user()

# Delete all sessions for a given user
def delete_all_sessions_for_user(user_id):
    db = get_db()
    db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    db.commit()

# Create a new session for a given user and return the session token
def create_session(user_id):
    token = secrets.token_urlsafe(32)
    expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)  # Session valid for 30 minutes
    db = get_db()
    db.execute("INSERT INTO sessions (token, user_id, expires) VALUES (?, ?, ?)", (token, user_id, expires))
    db.commit()
    return token

def get_user_from_session(token):
    db = get_db()
    cur = db.execute("SELECT user_id, expires FROM sessions WHERE token = ?", (token,))
    session = cur.fetchone()
    if session:
        if datetime.datetime.utcnow() > session['expires']:
            db.execute("DELETE FROM sessions WHERE token = ?", (token,))
            db.commit()
            return None
        cur = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = cur.fetchone()
        return user
    return None

def delete_session(token):
    db = get_db()
    db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    db.commit()

login_form = '''
<!doctype html>
<title>Login</title>
<h2>Login</h2>
<form method="post">
  <label>Username:</label>
  <input type="text" name="username"><br>
  <label>Password:</label>
  <input type="password" name="password"><br>
  <input type="submit" value="Login">
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user['password'], password):
            # Invalidate any existing sessions for this user
            delete_all_sessions_for_user(user['id'])
            token = create_session(user['id'])
            response = make_response(redirect(url_for('protected')))
            # Set the cookie with secure attributes:
            # - HttpOnly: prevents JavaScript access
            # - SameSite='Strict': helps protect against CSRF
            # - No domain attribute: makes it a host-only cookie (won't be sent to subdomains)
            response.set_cookie('session_token', token, httponly=True, samesite='Strict', secure=False)
            # Use secure=True when serving over HTTPS
            return response
        else:
            error = "Invalid username or password."
    return render_template_string(login_form, error=error)

@app.route('/protected')
def protected():
    token = request.cookies.get('session_token')
    if token:
        user = get_user_from_session(token)
        if user:
            return f"Hello, {user['username']}! You are logged in."
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    token = request.cookies.get('session_token')
    response = make_response(redirect(url_for('login')))
    if token:
        delete_session(token)
        response.set_cookie('session_token', '', expires=0)
    return response

@app.route('/')
def index():
    return redirect(url_for('protected'))

if __name__ == '__main__':
    # Manually call setup within the app context before starting the server
    with app.app_context():
        setup()
    app.run(debug=True)
