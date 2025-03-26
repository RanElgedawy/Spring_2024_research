from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Database Initialization
conn = sqlite3.connect('ecommerce.db', check_same_thread=False)
cursor = conn.cursor()

# Create users table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')
conn.commit()

# User Registration Endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Check if all required parameters are present
    if 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']

    # Check if username is already taken
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        return jsonify({'message': 'Username already exists'}), 400

    # Hash the password before storing in the database
    hashed_password = generate_password_hash(password)

    # Insert the new user into the database
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# User Login Endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Check if all required parameters are present
    if 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']

    # Retrieve user from the database based on username
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()

    # Check if the user exists and verify password
    if user and check_password_hash(user[2], password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

if __name__ == '__main__':
    app.run(debug=True)