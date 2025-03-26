from flask import Flask, request, redirect, url_for, render_template, make_response, g
import sqlite3
import hashlib

app = Flask(__name__)

# Database configuration
DATABASE = 'user_sessions.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def init_db():
    with app.app_context():
        db = get_db()
        # Create user table
        db.execute("DROP TABLE IF EXISTS users")
        db.execute("DROP TABLE IF EXISTS sessions")
        
        db.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL)''')
        # Create session table
        db.execute('''CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id))''')
        # Insert a test user (password is hashed)
        hashed_password = hashlib.sha256('password123'.encode()).hexdigest()
        db.execute('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)',
                   ('testuser', hashed_password))
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Helper function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Helper function to validate login
def validate_user(username, password):
    user = query_db('SELECT * FROM users WHERE username = ? AND password = ?',
                    (username, hash_password(password)), one=True)
    return user

# Helper function to create session
def create_session(user_id):
    import uuid
    session_id = str(uuid.uuid4())
    db = get_db()
    db.execute('INSERT INTO sessions (session_id, user_id) VALUES (?, ?)', (session_id, user_id))
    db.commit()
    return session_id

# Helper function to validate session
def validate_session(session_id):
    session = query_db('SELECT * FROM sessions WHERE session_id = ?', (session_id,), one=True)
    return session

# Route for home page
@app.route('/')
def home():
    session_id = request.cookies.get('session_id')
    if session_id and validate_session(session_id):
        return 'Welcome back, logged-in user!'
    return 'You are not logged in. <a href="/login">Login</a>'

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = validate_user(username, password)
        if user:
            session_id = create_session(user[0])
            response = make_response(redirect(url_for('home')))
            response.set_cookie('session_id', session_id, domain='localhost', httponly=True, samesite='Lax')
            return response
        else:
            return 'Invalid username or password'
    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

# Route for logout
@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('session_id', '', expires=0, domain='localhost')
    return response

if __name__ == '__main__':
    # Initialize the database and create tables
    init_db()
    # Run the Flask app
    app.run(debug=True)