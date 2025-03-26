from flask import Flask, request, jsonify, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'users.db'
app = Flask(__name__)

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def create_user_table():
    """Creates the users table if it doesn't exist."""
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
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    Expected JSON body: {"username": "desired_username", "password": "your_password"}
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    # Hash the password for secure storage.
    password_hash = generate_password_hash(password)
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)', 
            (username, password_hash)
        )
        db.commit()
        return jsonify({'message': 'User registered successfully.'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists.'}), 400

@app.route('/login', methods=['POST'])
def login():
    """
    Login a user.
    Expected JSON body: {"username": "your_username", "password": "your_password"}
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    
    if result is None:
        return jsonify({'error': 'Invalid username or password.'}), 401
    
    password_hash = result[0]
    if check_password_hash(password_hash, password):
        return jsonify({'message': 'Login successful.'}), 200
    else:
        return jsonify({'error': 'Invalid username or password.'}), 401

# A simple endpoint to list registered users for testing purposes.
@app.route('/test', methods=['GET'])
def test():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, username FROM users')
    users = cursor.fetchall()
    return jsonify({'users': users}), 200

if __name__ == '__main__':
    create_user_table()  # Automatically create the users table
    app.run(debug=True)
