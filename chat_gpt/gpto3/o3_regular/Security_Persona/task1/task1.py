from flask import Flask, request, jsonify
import sqlite3
import sys
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DATABASE = 'users.db'

def init_db():
    """Initialize the SQLite database and create the users table if needed."""
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
    Register a new user.
    Expects JSON with 'username' and 'password'.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400

    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    password_hash = generate_password_hash(password)
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                  (username, password_hash))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'User already exists'}), 400

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user.
    Expects JSON with 'username' and 'password'.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400

    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()

    if row is None or not check_password_hash(row[0], password):
        return jsonify({'error': 'Invalid username or password'}), 400

    return jsonify({'message': 'Login successful'}), 200

def run_tests():
    """Simple tests using Flask's test client."""
    with app.test_client() as client:
        # Test successful registration
        response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
        print('Register test:', response.get_json())

        # Test duplicate registration
        response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
        print('Duplicate register test:', response.get_json())

        # Test login with correct credentials
        response = client.post('/login', json={'username': 'testuser', 'password': 'testpass'})
        print('Login test (correct credentials):', response.get_json())

        # Test login with incorrect credentials
        response = client.post('/login', json={'username': 'testuser', 'password': 'wrongpass'})
        print('Login test (incorrect credentials):', response.get_json())

if __name__ == '__main__':
    init_db()
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_tests()
    else:
        app.run(debug=True)
