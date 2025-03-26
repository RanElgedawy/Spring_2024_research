from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sys

app = Flask(__name__)
DATABASE = 'users.db'

def init_db():
    """Initializes the database and creates the users table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/register', methods=['POST'])
def register():
    """
    Registers a new user.
    Expects JSON payload: {"username": "<username>", "password": "<password>"}
    Returns a success message or an error if the user already exists or data is missing.
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password required'}), 400
    
    username = data['username']
    password = data['password']
    password_hash = generate_password_hash(password)
    
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'User already exists'}), 400
    finally:
        conn.close()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Logs in a registered user.
    Expects JSON payload: {"username": "<username>", "password": "<password>"}
    Returns a success message if credentials are correct or an error otherwise.
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password required'}), 400
    
    username = data['username']
    password = data['password']
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    
    if row and check_password_hash(row[0], password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 400

def run_tests():
    """Runs simple tests using Flask's test client to demonstrate registration and login functionality."""
    with app.test_client() as client:
        print("Testing registration...")
        response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
        print('Register response:', response.json)
        
        print("Testing duplicate registration (should error)...")
        response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
        print('Duplicate register response:', response.json)
        
        print("Testing login with correct credentials...")
        response = client.post('/login', json={'username': 'testuser', 'password': 'testpass'})
        print('Login response:', response.json)
        
        print("Testing login with incorrect credentials...")
        response = client.post('/login', json={'username': 'testuser', 'password': 'wrongpass'})
        print('Login with wrong password response:', response.json)

if __name__ == '__main__':
    # Initialize the database and create tables if needed.
    init_db()
    
    # If you run the script with "test" as an argument, the built-in tests will execute.
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_tests()
    else:
        # Otherwise, start the Flask development server.
        app.run(debug=True)
