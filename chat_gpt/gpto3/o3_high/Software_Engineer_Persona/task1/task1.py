import sqlite3
import sys
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DATABASE = 'users.db'  # SQLite file for persistence

def get_db_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with a 'users' table."""
    conn = get_db_connection()
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    Expects JSON with 'username' and 'password'. Password is hashed before storing.
    Returns an error if the username already exists.
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    
    username = data['username']
    password = data['password']
    hashed_password = generate_password_hash(password)
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Username already exists'}), 400
    conn.close()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Log in an existing user.
    Expects JSON with 'username' and 'password'. Checks the password hash.
    Returns an error if credentials are invalid.
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400

    username = data['username']
    password = data['password']

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    if user is None or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 400
    
    return jsonify({'message': 'Logged in successfully'}), 200

if __name__ == '__main__':
    init_db()  # Ensure the database and tables are created

    # If "test" is provided as a command-line argument, run basic tests using Flask's test client.
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("Running built-in tests...")
        with app.test_client() as client:
            # Test registration with missing fields
            response = client.post('/register', json={})
            print('Register missing fields:', response.json)

            # Test successful registration
            response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
            print('Register test user:', response.json)

            # Test duplicate registration
            response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
            print('Register duplicate:', response.json)

            # Test login with wrong password
            response = client.post('/login', json={'username': 'testuser', 'password': 'wrongpass'})
            print('Login wrong password:', response.json)

            # Test login with correct credentials
            response = client.post('/login', json={'username': 'testuser', 'password': 'testpass'})
            print('Login success:', response.json)
    else:
        # Run the Flask app normally
        app.run(debug=True)
