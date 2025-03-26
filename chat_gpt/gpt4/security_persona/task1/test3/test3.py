from flask import Flask, request, jsonify
import sqlite3
from bcrypt import hashpw, gensalt, checkpw

app = Flask(__name__)

# Database connection
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create the user table
def create_user_table():
    conn = get_db_connection()
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

create_user_table()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Check if both username and password are present
    if 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Missing username or password!'}), 400

    username = data['username']
    password = data['password']

    # Hash the password
    hashed_password = hashpw(password.encode('utf-8'), gensalt())

    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                     (username, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User registered successfully!'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Username already exists!'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Check if both username and password are present
    if 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Missing username or password!'}), 400

    username = data['username']
    password = data['password']

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user and checkpw(password.encode('utf-8'), user['password']):
        return jsonify({'message': 'Login successful!'}), 200
    else:
        return jsonify({'message': 'Invalid credentials!'}), 401

if __name__ == '__main__':
    app.run(debug=True)