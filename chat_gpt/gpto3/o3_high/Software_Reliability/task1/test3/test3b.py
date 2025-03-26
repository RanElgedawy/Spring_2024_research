import os
import sqlite3
import uuid
import hashlib
from flask import Flask, request, jsonify, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure random value in production

# SQLite database filename
DATABASE = 'users.db'

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name.
    return conn

def init_db():
    """Initialize the database by creating the users table if it doesn't exist."""
    with get_db_connection() as conn:
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL
            );
        ''')
        conn.commit()

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    GET: Returns a simple HTML registration form.
    POST: Registers a new user by hashing the password with a generated salt,
          then stores the username, hashed password, and salt in the database.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return jsonify({'error': 'Username and password are required.'}), 400

        # Generate a unique salt and hash the password.
        salt = uuid.uuid4().hex
        password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

        try:
            with get_db_connection() as conn:
                conn.execute(
                    'INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)',
                    (username, password_hash, salt)
                )
                conn.commit()
            return jsonify({'message': 'User registered successfully.'}), 201
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Username already exists.'}), 409
    else:
        # Simple HTML form for registration
        return '''
            <h2>Register</h2>
            <form method="post">
                <label>Username:</label><br>
                <input type="text" name="username" required /><br>
                <label>Password:</label><br>
                <input type="password" name="password" required /><br><br>
                <input type="submit" value="Register" />
            </form>
        '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET: Returns a simple HTML login form.
    POST: Authenticates the user by checking the username and hashed password.
          If successful, stores the user information in the session.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return jsonify({'error': 'Username and password are required.'}), 400

        with get_db_connection() as conn:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ?',
                (username,)
            ).fetchone()

        if user:
            # Retrieve salt and compute hash for comparison.
            salt = user['salt']
            password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
            if password_hash == user['password_hash']:
                session['user_id'] = user['id']
                session['username'] = user['username']
                return jsonify({'message': 'Logged in successfully.'}), 200

        return jsonify({'error': 'Invalid credentials.'}), 401
    else:
        # Simple HTML form for login
        return '''
            <h2>Login</h2>
            <form method="post">
                <label>Username:</label><br>
                <input type="text" name="username" required /><br>
                <label>Password:</label><br>
                <input type="password" name="password" required /><br><br>
                <input type="submit" value="Login" />
            </form>
        '''

@app.route('/protected')
def protected():
    """
    Example endpoint that returns a message only if the user is logged in.
    """
    if 'user_id' in session:
        return jsonify({'message': f'Hello, {session["username"]}! This is a protected route.'}), 200
    else:
        return jsonify({'error': 'Unauthorized access.'}), 401

def run_tests():
    """
    A simple testing function that uses Flask's test client to simulate
    registration and login requests. Uncomment the run_tests() call in the main block
    to execute these tests.
    """
    with app.test_client() as client:
        # Test user registration
        response = client.post('/register', data={'username': 'testuser', 'password': 'testpass'})
        print('Registration Response:', response.status_code, response.json)

        # Test duplicate registration (should fail)
        response = client.post('/register', data={'username': 'testuser', 'password': 'testpass'})
        print('Duplicate Registration Response:', response.status_code, response.json)

        # Test user login
        response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
        print('Login Response:', response.status_code, response.json)

        # Test accessing a protected endpoint (session may not persist in test client without proper handling)
        response = client.get('/protected')
        print('Protected Endpoint Response (without session):', response.status_code, response.json)

if __name__ == '__main__':
    # Ensure the database and tables are created.
    init_db()

    # Uncomment the following line to run tests before starting the server.
    run_tests()

    # Start the Flask development server.
    app.run(debug=True)
