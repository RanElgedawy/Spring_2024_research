import uuid
import sqlite3
from flask import Flask, request, jsonify, make_response, g

app = Flask(__name__)
DATABASE = 'app.db'

# Utility functions for database connection and initialization
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create a simple users table (username, password)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        # Create a sessions table to store login sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                session_token TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # Insert a test user (username: testuser, password: password)
        cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", 
                       ("testuser", "password"))
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Route for logging in users
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Missing credentials'}), 400

    db = get_db()
    cursor = db.cursor()
    # Check if the user exists with matching credentials
    cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    row = cursor.fetchone()
    if row is None:
        return jsonify({'message': 'Invalid credentials'}), 401
    
    user_id = row[0]
    # Generate a unique session token
    session_token = str(uuid.uuid4())
    cursor.execute("INSERT INTO sessions (user_id, session_token) VALUES (?, ?)", (user_id, session_token))
    db.commit()

    # Create a response and set the session cookie
    # By NOT setting a domain, the cookie is host-only and will not work for subdomains.
    response = make_response(jsonify({'message': 'Logged in successfully'}))
    response.set_cookie('session_token', session_token, httponly=True, samesite='Lax')
    return response

# Utility function to validate the session cookie
def validate_session():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return None
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM sessions WHERE session_token=?", (session_token,))
    row = cursor.fetchone()
    if row is None:
        return None
    return row[0]

# A protected route that requires a valid session cookie
@app.route('/protected')
def protected():
    user_id = validate_session()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    return jsonify({'message': f'Hello user {user_id}, you are logged in.'})

# Entry point to initialize the database and run the Flask server
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
