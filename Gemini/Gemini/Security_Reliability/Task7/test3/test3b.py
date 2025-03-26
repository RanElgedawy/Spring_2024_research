from flask import Flask, request, make_response, jsonify, g
import secrets
import sqlite3
import hashlib

app = Flask(__name__)

# Database configuration
DATABASE = 'users.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_db(error):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Create the database table if it doesn't exist
def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.executescript(f.read())
    db.commit()

# Create a schema.sql file with the following content:
# CREATE TABLE users (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     username TEXT UNIQUE NOT NULL,
#     password TEXT NOT NULL,
#     session_token TEXT
# );

# Generate a secure session token
def generate_session_token():
    return secrets.token_urlsafe(32)

# Hash the password using a strong algorithm (e.g., bcrypt)
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Login endpoint
@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user and hash_password(password) == user[1]:
        session_token = generate_session_token()
        cursor.execute("UPDATE users SET session_token = ? WHERE id = ?", (session_token, user[0]))
        db.commit()

        response = make_response(jsonify({'message': 'Login successful'}))
        response.set_cookie('session_token', session_token, httponly=True, samesite='Lax')
        return response

    return jsonify({'message': 'Login failed'}), 401

# Protected endpoint (requires authentication)
@app.route('/protected', methods=['GET'])
def protected():
    session_token = request.cookies.get('session_token')

    if session_token:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE session_token = ?", (session_token,))
        user = cursor.fetchone()

        if user:
            return jsonify({'message': 'You are logged in'})

    return jsonify({'message': 'Unauthorized'}), 401

# Test the functionality
if __name__ == '__main__':
    init_db()
    app.run(debug=True)