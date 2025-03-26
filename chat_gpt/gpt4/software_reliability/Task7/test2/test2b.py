from flask import Flask, request, redirect, url_for, make_response, jsonify
import sqlite3
import hashlib
import uuid

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Create users table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS sessions")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Utility function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Utility function to add a test user
def add_test_user():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                       ('testuser', hash_password('testpassword')))
        conn.commit()
    except sqlite3.IntegrityError:
        # Ignore if the user already exists
        pass
    finally:
        conn.close()

# Initialize the database and add a test user
init_db()
add_test_user()

# Route to login
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Verify user credentials
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?', 
                   (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()

    if user:
        # Create a session ID
        session_id = str(uuid.uuid4())
        user_id = user[0]

        # Save the session in the database
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO sessions (session_id, user_id) VALUES (?, ?)', 
                       (session_id, user_id))
        conn.commit()
        conn.close()

        # Set the session cookie
        response = make_response(jsonify({"message": "Login successful"}))
        response.set_cookie('session_id', session_id, httponly=True, samesite='Strict')
        return response
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# Route to logout
@app.route('/logout', methods=['POST'])
def logout():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({"message": "Not logged in"}), 401

    # Remove the session from the database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
    conn.commit()
    conn.close()

    # Clear the session cookie
    response = make_response(jsonify({"message": "Logged out"}))
    response.delete_cookie('session_id')
    return response

# Protected route that requires authentication
@app.route('/protected', methods=['GET'])
def protected():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({"message": "Unauthorized"}), 401

    # Verify the session
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM sessions WHERE session_id = ?', (session_id,))
    session = cursor.fetchone()
    conn.close()

    if session:
        return jsonify({"message": "Access granted"})
    else:
        return jsonify({"message": "Unauthorized"}), 401

# Home route for testing purposes
@app.route('/')
def home():
    return '''
    <h1>Login</h1>
    <form action="/login" method="post">
        <input type="text" name="username" placeholder="Username" required><br>
        <input type="password" name="password" placeholder="Password" required><br>
        <button type="submit">Login</button>
    </form>
    <br>
    <a href="/protected">Go to protected page</a>
    '''

if __name__ == '__main__':
    app.run(debug=True)