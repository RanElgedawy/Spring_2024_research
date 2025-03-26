from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
import sqlite3
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'mysecretkey'
bcrypt = Bcrypt(app)

# Define the database file path
DATABASE = 'ecommerce.db'

# Function to get a database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

# Function to create the users table if it doesn't exist
def create_tables():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Initialize and create tables
@app.before_first_request
def initialize():
    create_tables()

# Register a new user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Username already exists'}), 409
    finally:
        conn.close()

    return jsonify({'message': 'User registered successfully'}), 201

# Login a registered user
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()

    if row and bcrypt.check_password_hash(row[0], password):
        session['user'] = username
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

# Logout the user
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# Test the functionality
@app.route('/test', methods=['GET'])
def test():
    if 'user' in session:
        return jsonify({'message': f'Logged in as {session["user"]}'})
    return jsonify({'message': 'Not logged in'})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)