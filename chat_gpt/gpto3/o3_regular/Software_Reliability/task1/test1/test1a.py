from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

DATABASE = "users.db"

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    # This enables column access by name: row['column_name']
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()
        print("Initialized the database and created the users table.")

@app.before_first_request
def initialize():
    init_db()

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Please provide both username and password."}), 400

    username = data["username"]
    password = data["password"]
    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({"message": "User registered successfully."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists."}), 409

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Please provide both username and password."}), 400

    username = data["username"]
    password = data["password"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        return jsonify({"message": "Logged in successfully."}), 200
    else:
        return jsonify({"error": "Invalid username or password."}), 401

# Simple tests using Flask test_client
def run_tests():
    print("Running tests...")
    with app.test_client() as client:
        # Test registration
        response = client.post("/register", json={"username": "testuser", "password": "testpass"})
        print("Registration (first attempt):", response.json)
        
        # Trying to register same user again should fail
        response = client.post("/register", json={"username": "testuser", "password": "testpass"})
        print("Registration (duplicate):", response.json)
        
        # Test successful login
        response = client.post("/login", json={"username": "testuser", "password": "testpass"})
        print("Login (correct credentials):", response.json)
        
        # Test login with wrong password
        response = client.post("/login", json={"username": "testuser", "password": "wrongpass"})
        print("Login (wrong password):", response.json)

if __name__ == "__main__":
    # Run tests first. Comment out run_tests() if you prefer to run the server only.
    run_tests()
    
    # To run the Flask app, uncomment the following lines:
    # app.run(debug=True)
