from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
DATABASE = "users.db"

def init_db():
    """Initializes the database and creates the users table if not exists."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        conn.commit()

def add_user(username, password):
    """Registers a new user with a hashed password."""
    password_hash = generate_password_hash(password)
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            return True, "User registered successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists."

def verify_user(username, password):
    """Verifies a user's credentials."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result:
            stored_hash = result[0]
            if check_password_hash(stored_hash, password):
                return True
    return False

@app.route('/register', methods=['POST'])
def register():
    """Endpoint to register a new user.
       Expected JSON payload: {"username": "your_username", "password": "your_password"}
    """
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password required"}), 400

    success, message = add_user(data['username'], data['password'])
    if success:
        return jsonify({"message": message}), 201
    else:
        return jsonify({"error": message}), 400

@app.route('/login', methods=['POST'])
def login():
    """Endpoint to login a user.
       Expected JSON payload: {"username": "your_username", "password": "your_password"}
    """
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password required"}), 400

    if verify_user(data['username'], data['password']):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

if __name__ == '__main__':
    # Initialize the database and run the app.
    init_db()
    print("Database initialized and ready.")
    print("You can test registration and login by sending POST requests to /register and /login endpoints.")
    print("Example using curl:")
    print('  curl -X POST -H "Content-Type: application/json" -d \'{"username": "alice", "password": "secret"}\' http://127.0.0.1:5000/register')
    print('  curl -X POST -H "Content-Type: application/json" -d \'{"username": "alice", "password": "secret"}\' http://127.0.0.1:5000/login')
    app.run(debug=True)
