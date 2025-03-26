from flask import Flask, request, jsonify, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Database helper functions
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Connect to the database, ensuring foreign keys are enabled
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    # Create users table if it does not exist
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Route to register a new user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    username = data['username']
    password = data['password']
    password_hash = generate_password_hash(password)

    db = get_db()
    try:
        db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        db.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 409

# Route to login an existing user
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    username = data['username']
    password = data['password']
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    if user and check_password_hash(user['password_hash'], password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

# Test endpoint to check server status
@app.route('/')
def index():
    return "E-commerce Platform API is running!"

# Test functionality automatically when run as a script
def run_tests():
    with app.test_client() as client:
        # Test registration
        response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
        print("Registration response:", response.status_code, response.get_json())

        # Test duplicate registration
        response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
        print("Duplicate registration response:", response.status_code, response.get_json())

        # Test login success
        response = client.post('/login', json={'username': 'testuser', 'password': 'testpass'})
        print("Login success response:", response.status_code, response.get_json())

        # Test login failure
        response = client.post('/login', json={'username': 'testuser', 'password': 'wrongpass'})
        print("Login failure response:", response.status_code, response.get_json())

if __name__ == '__main__':
    # Initialize the database
    init_db()

    # Uncomment the next line to run tests when starting the script
    run_tests()

    # Run the Flask development server
    app.run(debug=True)
