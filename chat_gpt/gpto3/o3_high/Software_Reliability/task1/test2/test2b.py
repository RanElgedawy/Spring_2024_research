from flask import Flask, request, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DATABASE = 'users.db'

def init_db():
    """Initializes the database and creates the users table if it does not exist."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                 )''')
    conn.commit()
    conn.close()

@app.route('/register', methods=['POST'])
def register():
    """Registers a new user with a username and password."""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    username = data['username']
    password = data['password']
    hashed_password = generate_password_hash(password)

    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User registered successfully!'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 409

@app.route('/login', methods=['POST'])
def login():
    """Authenticates a user with their username and password."""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    username = data['username']
    password = data['password']

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if row and check_password_hash(row[0], password):
        return jsonify({'message': 'Login successful!'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

def run_tests():
    """Runs a simple test suite using Flask's test client."""
    # Ensure a fresh DB for testing
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    init_db()

    with app.test_client() as client:
        # Test successful registration
        response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
        print('Register:', response.status_code, response.get_json())

        # Test duplicate registration
        response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
        print('Register duplicate:', response.status_code, response.get_json())

        # Test login with correct credentials
        response = client.post('/login', json={'username': 'testuser', 'password': 'testpass'})
        print('Login (correct):', response.status_code, response.get_json())

        # Test login with incorrect password
        response = client.post('/login', json={'username': 'testuser', 'password': 'wrongpass'})
        print('Login (wrong password):', response.status_code, response.get_json())

if __name__ == '__main__':
    init_db()
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_tests()
    else:
        app.run(debug=True)
