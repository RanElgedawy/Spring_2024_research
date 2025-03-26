from flask import Flask, request, jsonify, session, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure secret in production
DATABASE = 'users.db'

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    """Initializes the database by creating the users table if it doesn't exist."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        db.commit()
        print("Database initialized and users table created (if not exists).")

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/register', methods=['POST'])
def register():
    """
    Registers a new user.
    Expects JSON data with 'username', 'email', and 'password'.
    Passwords are securely hashed before storing.
    """
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'Missing fields: username, email, and password are required.'}), 400

    password_hash = generate_password_hash(password)
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", 
                       (username, email, password_hash))
        db.commit()
        return jsonify({'message': 'User registered successfully.'})
    except sqlite3.IntegrityError as e:
        # Likely a duplicate username or email.
        return jsonify({'error': 'Username or email already exists.'}), 400

@app.route('/login', methods=['POST'])
def login():
    """
    Logs in a user.
    Expects JSON data with 'username' and 'password'.
    Validates the credentials against the stored password hash.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Missing fields: username and password are required.'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user is None or not check_password_hash(user[2], password):
        return jsonify({'error': 'Invalid username or password.'}), 401

    # Set a session (in a real application, consider using JWTs or another mechanism)
    session['user_id'] = user[0]
    return jsonify({'message': 'Logged in successfully.'})

@app.route('/test', methods=['GET'])
def test():
    """
    A simple test page that explains how to test the endpoints.
    You can use tools like curl or Postman to POST JSON data to /register and /login.
    """
    return '''
        <h1>Registration and Login API Test</h1>
        <p>Use the following curl commands to test the functionality:</p>
        <pre>
# Register a new user
curl -X POST -H "Content-Type: application/json" \\
     -d '{"username":"user1", "email": "user1@example.com", "password": "password123"}' \\
     http://127.0.0.1:5000/register

# Log in as the user
curl -X POST -H "Content-Type: application/json" \\
     -d '{"username":"user1", "password": "password123"}' \\
     http://127.0.0.1:5000/login
        </pre>
    '''

if __name__ == '__main__':
    init_db()  # Create the database and table automatically
    app.run(debug=True)
