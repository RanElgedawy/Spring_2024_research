from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import sys

app = Flask(__name__)
DATABASE = 'users.db'

def init_db():
    """Initialize the database and create the users table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''
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
    User registration endpoint.
    Expects JSON with "username" and "password".
    Returns a success message on registration or an error if the username exists.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    # Hash the password before storing it
    hashed_password = generate_password_hash(password)

    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'User already exists'}), 400

@app.route('/login', methods=['POST'])
def login():
    """
    User login endpoint.
    Expects JSON with "username" and "password".
    Returns a success message if credentials are correct, otherwise an error.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()

    if result and check_password_hash(result[0], password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

def run_tests():
    """Run basic tests using Flask's test client."""
    with app.test_client() as client:
        # Test registration of a new user
        response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
        print('Register:', response.status_code, response.get_json())

        # Test duplicate registration (should fail)
        response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
        print('Duplicate register:', response.status_code, response.get_json())

        # Test login with correct credentials
        response = client.post('/login', json={'username': 'testuser', 'password': 'testpass'})
        print('Login:', response.status_code, response.get_json())

        # Test login with incorrect password
        response = client.post('/login', json={'username': 'testuser', 'password': 'wrongpass'})
        print('Login with wrong password:', response.status_code, response.get_json())

if __name__ == '__main__':
    init_db()
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_tests()
    else:
        app.run(debug=True)
