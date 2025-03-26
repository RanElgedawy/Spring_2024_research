from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

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
                password_hash TEXT NOT NULL
            )
        ''')
    conn.close()

@app.route('/register', methods=['POST'])
def register():
    # Expecting JSON with "username" and "password"
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required.'}), 400

    username = data['username']
    password = data['password']
    # Securely hash the password
    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists.'}), 400
    finally:
        conn.close()

    return jsonify({'message': 'User registered successfully.'}), 201

@app.route('/login', methods=['POST'])
def login():
    # Expecting JSON with "username" and "password"
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required.'}), 400

    username = data['username']
    password = data['password']

    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()
    conn.close()

    if user is None or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid username or password.'}), 401

    return jsonify({'message': 'Logged in successfully.'}), 200

@app.route('/')
def index():
    return '''
        <h1>User Registration and Login</h1>
        <p>To register, send a POST request to /register with JSON {"username": "your_username", "password": "your_password"}.</p>
        <p>To log in, send a POST request to /login with the same JSON format.</p>
    '''

if __name__ == '__main__':
    init_db()  # Automatically create the table if it doesn't exist
    app.run(debug=True)
