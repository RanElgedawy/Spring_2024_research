import sqlite3
from flask import Flask, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'users.db'

app = Flask(__name__)

# --- Database helper functions ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Connect to the SQLite database file
        db = g._database = sqlite3.connect(DATABASE)
        # Return rows as dictionaries
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Create the users table if it doesn't exist."""
    with app.app_context():
        db = get_db()
        db.execute("DROP TABLE IF EXISTS users")
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Routes ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Validate input
    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    # Hash the password for security
    hashed_password = generate_password_hash(password)
    
    try:
        db = get_db()
        db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists.'}), 400

    return jsonify({'message': f'User {username} registered successfully.'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Validate input
    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    if user and check_password_hash(user['password'], password):
        return jsonify({'message': f'User {username} logged in successfully.'}), 200
    else:
        return jsonify({'error': 'Invalid username or password.'}), 401

# --- Test Functionality ---
# This function uses Flask's test client to demonstrate the registration and login endpoints.
def run_tests():
    with app.test_client() as client:
        print("Testing user registration and login:")

        # Test registration
        response = client.post('/register', json={'username': 'john_doe', 'password': 'securepass'})
        print('Registration response:', response.get_json())

        # Try registering the same user again
        response = client.post('/register', json={'username': 'john_doe', 'password': 'securepass'})
        print('Duplicate registration response:', response.get_json())

        # Test successful login
        response = client.post('/login', json={'username': 'john_doe', 'password': 'securepass'})
        print('Login response:', response.get_json())

        # Test login with wrong password
        response = client.post('/login', json={'username': 'john_doe', 'password': 'wrongpass'})
        print('Login with wrong password response:', response.get_json())

if __name__ == '__main__':
    init_db()
    # Uncomment the next line to run tests when executing the script.
    run_tests()
    app.run(debug=True)
