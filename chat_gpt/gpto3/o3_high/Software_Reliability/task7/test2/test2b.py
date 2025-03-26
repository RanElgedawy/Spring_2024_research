from flask import Flask, request, jsonify, make_response, g
import sqlite3
import secrets

DATABASE = 'app.db'

def get_db():
    """Get a connection to the SQLite database, stored in the Flask global context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    """Initialize the database with users and sessions tables.
       Also insert a default test user if one does not already exist."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS sessions")
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    db.commit()
    # Insert a test user (username: test, password: password) if not already present
    cursor.execute("SELECT * FROM users WHERE username = ?", ("test",))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("test", "password"))
        db.commit()
    db.close()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Used if you need to sign cookies

@app.before_request
def before_request():
    """Open a database connection before each request."""
    g.db = get_db()

@app.teardown_request
def teardown_request(exception):
    """Close the database connection after each request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def verify_session(token):
    """Verify if a session token exists in the sessions table and return the associated user_id."""
    cursor = g.db.cursor()
    cursor.execute("SELECT user_id FROM sessions WHERE token = ?", (token,))
    result = cursor.fetchone()
    return result[0] if result else None

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint.
       Expects JSON with 'username' and 'password'.
       If credentials match, creates a session and sets a host-only cookie."""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    cursor = g.db.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user and user[1] == password:
        user_id = user[0]
        token = secrets.token_hex(16)  # Generate a random session token
        cursor.execute("INSERT INTO sessions (user_id, token) VALUES (?, ?)", (user_id, token))
        g.db.commit()
        response = make_response(jsonify({"message": "Logged in successfully"}))
        # Set a cookie named 'session_id'
        # Not providing a domain ensures the cookie is valid only for the current host
        response.set_cookie("session_id", token, httponly=True, samesite='Lax')
        return response
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/profile', methods=['GET'])
def profile():
    """Protected endpoint that checks for a valid session cookie.
       Returns a welcome message if the user is authenticated."""
    token = request.cookies.get("session_id")
    if not token:
        return jsonify({"message": "Not logged in"}), 401
    user_id = verify_session(token)
    if not user_id:
        return jsonify({"message": "Invalid session"}), 401
    cursor = g.db.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    return jsonify({"message": f"Welcome, {user[0]}!"})

@app.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint.
       Deletes the session from the database and clears the cookie."""
    token = request.cookies.get("session_id")
    if token:
        cursor = g.db.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        g.db.commit()
    response = make_response(jsonify({"message": "Logged out"}))
    response.delete_cookie("session_id")
    return response

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
