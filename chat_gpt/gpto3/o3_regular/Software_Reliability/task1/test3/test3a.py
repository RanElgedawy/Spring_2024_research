import sqlite3
from flask import Flask, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DATABASE = 'users.db'

# --- Database Utilities ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        # Create a table if it doesn't exist.
        db.execute("DROP TABLE IF EXISTS users")
        db.execute('''
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

# --- Helper Functions ---
def add_user(username, password):
    db = get_db()
    password_hash = generate_password_hash(password)
    try:
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                   (username, password_hash))
        db.commit()
        return True, "User registered successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists."

def verify_user(username, password):
    db = get_db()
    cur = db.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if row and check_password_hash(row["password_hash"], password):
        return True
    return False

# --- Routes ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    success, message = add_user(username, password)
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message': message}), status_code

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    if verify_user(username, password):
        return jsonify({'success': True, 'message': 'Login successful.'})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials.'}), 401

# --- Testing Functionality ---
# Run tests by calling test() function (or run this file with argument "test")
def test():
    import json
    with app.test_client() as client:
        # Ensure clean start
        with app.app_context():
            db = get_db()
            db.execute("DROP TABLE IF EXISTS users")
            init_db()

        # Test registration
        response = client.post('/register', json={'username': 'alice', 'password': 'password123'})
        print('Register alice:', response.get_json())

        # Attempt duplicate registration
        response = client.post('/register', json={'username': 'alice', 'password': 'newpassword'})
        print('Register duplicate alice:', response.get_json())

        # Test login success
        response = client.post('/login', json={'username': 'alice', 'password': 'password123'})
        print('Login alice:', response.get_json())

        # Test login failure
        response = client.post('/login', json={'username': 'alice', 'password': 'wrongpassword'})
        print('Login alice with wrong password:', response.get_json())

if __name__ == '__main__':
    import sys
    init_db()
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        app.run(debug=True)
