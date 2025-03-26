from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import sys

app = Flask(__name__)
DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        ''')
    conn.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required.'}), 400

    username = data['username']
    password = data['password']
    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, hashed_password)
            )
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists.'}), 409
    finally:
        conn.close()

    return jsonify({'message': 'User registered successfully.'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required.'}), 400

    username = data['username']
    password = data['password']

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        return jsonify({'message': 'Login successful.'}), 200
    else:
        return jsonify({'error': 'Invalid username or password.'}), 401

# Simple test routine using Flask's test_client
def run_tests():
    with app.test_client() as client:
        print("Testing registration of 'testuser'...")
        response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
        print('Register:', response.get_json())

        print("Testing duplicate registration for 'testuser'...")
        response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
        print('Duplicate Register:', response.get_json())

        print("Testing login with correct credentials...")
        response = client.post('/login', json={'username': 'testuser', 'password': 'testpass'})
        print('Login (success):', response.get_json())

        print("Testing login with incorrect password...")
        response = client.post('/login', json={'username': 'testuser', 'password': 'wrongpass'})
        print('Login (failure):', response.get_json())

if __name__ == '__main__':
    init_db()
    # Run tests if the script is invoked with the "test" argument,
    # e.g., python script.py test
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_tests()
    else:
        app.run(debug=True)
