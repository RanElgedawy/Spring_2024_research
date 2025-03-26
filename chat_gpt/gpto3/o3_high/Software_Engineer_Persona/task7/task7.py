from flask import Flask, request, redirect, url_for, make_response, g
import sqlite3
import uuid
import datetime

app = Flask(__name__)
DATABASE = 'app.db'
SESSION_DURATION_SECONDS = 3600  # Session duration set to 1 hour

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    """Execute a query and return the result as a list of dictionaries."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database and creates the necessary tables if they don't exist."""
    db = get_db()
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("DROP TABLE IF EXISTS sessions")
    # Create the users table
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    ''')
    # Create the sessions table with an expiration column.
    db.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE,
            expires TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    ''')
    db.commit()
    # Seed a default user for testing if one doesn't exist
    user = query_db('SELECT * FROM users WHERE username = ?', ['test'], one=True)
    if user is None:
        db.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('test', 'testpass'))
        db.commit()

with app.app_context():
    init_db()

@app.route('/')
def index():
    """Home page with a login form and a link to the protected page."""
    return '''
    <h1>Login</h1>
    <form action="/login" method="post">
        Username: <input name="username" type="text" /><br/>
        Password: <input name="password" type="password" /><br/>
        <input type="submit" value="Login" />
    </form>
    <br/>
    <a href="/protected">Go to Protected Page</a>
    '''

@app.route('/login', methods=['POST'])
def login():
    """Handle user login: invalidate previous sessions, create a new session with expiration, and set the cookie."""
    username = request.form.get('username')
    password = request.form.get('password')
    user = query_db('SELECT * FROM users WHERE username = ? AND password = ?', [username, password], one=True)
    if user:
        db = get_db()
        # Invalidate previous sessions for this user.
        db.execute('DELETE FROM sessions WHERE user_id = ?', (user['id'],))
        db.commit()
        # Create a new session token and expiration time using timezone-aware datetime.
        session_token = str(uuid.uuid4())
        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=SESSION_DURATION_SECONDS)
        db.execute('INSERT INTO sessions (user_id, session_token, expires) VALUES (?, ?, ?)',
                   (user['id'], session_token, expiration.isoformat()))
        db.commit()
        response = make_response(redirect(url_for('protected')))
        # Set the session cookie with max_age so that it expires after one hour.
        response.set_cookie('session', session_token, httponly=True, max_age=SESSION_DURATION_SECONDS)
        return response
    else:
        return 'Invalid credentials', 401

def validate_session():
    """Checks if the session cookie is valid (and unexpired) and returns the associated user, or None if invalid."""
    session_token = request.cookies.get('session')
    if not session_token:
        return None
    session = query_db('SELECT * FROM sessions WHERE session_token = ?', [session_token], one=True)
    if session:
        # Parse the stored expiration timestamp into a timezone-aware datetime object.
        expiration_time = datetime.datetime.fromisoformat(session['expires'])
        if expiration_time < datetime.datetime.now(datetime.timezone.utc):
            # Session expired; remove it from the database.
            db = get_db()
            db.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
            db.commit()
            return None
        user = query_db('SELECT * FROM users WHERE id = ?', [session['user_id']], one=True)
        return user
    return None

@app.route('/protected')
def protected():
    """A protected route that requires a valid (and unexpired) session cookie."""
    user = validate_session()
    if user:
        return f'<h1>Welcome, {user["username"]}!</h1><p>Your session is active.</p><a href="/logout">Logout</a>'
    else:
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Logs out the user by deleting the session from the database and clearing the cookie."""
    session_token = request.cookies.get('session')
    if session_token:
        db = get_db()
        db.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
        db.commit()
    response = make_response(redirect(url_for('index')))
    response.delete_cookie('session')
    return response

if __name__ == '__main__':
    app.run(debug=True)
