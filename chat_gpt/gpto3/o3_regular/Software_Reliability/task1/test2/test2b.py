import os
import sqlite3
import sys
from flask import Flask, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

# Configuration
DATABASE = 'users.db'
DEBUG = True

# Create the Flask app
app = Flask(__name__)
app.config.from_object(__name__)

def get_db():
    """Opens a new database connection if one does not exist for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        # Enable dictionary access for rows.
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Creates the users table if it does not already exist."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.before_first_request
def initialize():
    init_db()

@app.route('/register', methods=['POST'])
def register():
    """
    Expects JSON payload with: username, email, password.
    Registers a new user if the username and email are unique.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "username, email and password are required"}), 400

    db = get_db()
    cursor = db.cursor()

    # Check if username or email already exists
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
    if cursor.fetchone():
        return jsonify({"error": "User with given username or email already exists"}), 400

    hashed_password = generate_password_hash(password)
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        db.commit()
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Expects JSON payload with: username and password.
    Checks credentials and returns a success message if valid.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user and check_password_hash(user["password"], password):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

# Optional testing functionality using Flask's test client.
def run_tests():
    print("Running tests...")
    with app.test_client() as client:
        # Test registration
        test_user = {"username": "testuser", "email": "test@example.com", "password": "testpass"}
        response = client.post("/register", json=test_user)
        print("Register response:", response.json)
        
        # Try registering the same user again to test duplicate handling
        response_dup = client.post("/register", json=test_user)
        print("Duplicate registration response:", response_dup.json)
        
        # Test login with correct credentials
        login_data = {"username": "testuser", "password": "testpass"}
        login_response = client.post("/login", json=login_data)
        print("Login response (correct credentials):", login_response.json)
        
        # Test login with wrong credentials
        wrong_login = {"username": "testuser", "password": "wrongpass"}
        wrong_login_response = client.post("/login", json=wrong_login)
        print("Login response (wrong credentials):", wrong_login_response.json)

if __name__ == '__main__':
    # If run with "test" as argument, run tests.
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        with app.app_context():
            # Ensure database is initialized for tests
            init_db()
        run_tests()
    else:
        # Run the Flask development server
        app.run(debug=True)
