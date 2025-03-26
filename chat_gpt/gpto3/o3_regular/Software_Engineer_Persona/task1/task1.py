import os
import sqlite3
import sys
from flask import Flask, request, jsonify, g, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key
DATABASE = 'users.db'

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Creates the users table if it doesn't exist."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    db.commit()

@app.route('/register', methods=['POST'])
def register():
    """
    Registers a new user.
    Expected JSON payload: {"username": "user", "email": "user@example.com", "password": "secret"}
    """
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Missing fields (username, email, password are required)'}), 400

    hashed_password = generate_password_hash(password)
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        return jsonify({'error': str(e)}), 400

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Logs in a registered user.
    Expected JSON payload: {"username": "user", "password": "secret"}
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user is None:
        return jsonify({'error': 'Invalid username or password'}), 400

    user_id, hashed_password = user
    if not check_password_hash(hashed_password, password):
        return jsonify({'error': 'Invalid username or password'}), 400

    session['user_id'] = user_id
    return jsonify({'message': 'Logged in successfully'}), 200

def run_tests():
    """Simple tests using Flask's test client."""
    with app.test_client() as client:
        print("Running tests...")

        # Test registration
        reg_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123'
        }
        response = client.post('/register', json=reg_data)
        print('Registration response:', response.get_json())

        # Test duplicate registration
        duplicate_response = client.post('/register', json=reg_data)
        print('Duplicate registration response:', duplicate_response.get_json())

        # Test login with correct credentials
        login_data = {
            'username': 'testuser',
            'password': 'password123'
        }
        response = client.post('/login', json=login_data)
        print('Login response (correct credentials):', response.get_json())

        # Test login with wrong credentials
        wrong_login = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = client.post('/login', json=wrong_login)
        print('Login response (wrong credentials):', response.get_json())

if __name__ == '__main__':
    # Manually initialize the database before starting the server or tests.
    with app.app_context():
        init_db()
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        run_tests()
    else:
        app.run(debug=True)
