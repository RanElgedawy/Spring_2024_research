from flask import Flask, request, make_response, jsonify
import secrets
import sqlite3
import datetime

app = Flask(__name__)

# Create a database connection
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    return conn

# Create the database table if it doesn't exist
def init_db():
    conn = get_db_connection()
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, session_token TEXT, expires TEXT)')


    # Insert test users
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('testuser1', 'testpassword1'))
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('testuser2', 'testpassword2'))
    
    conn.commit()
    conn.close()

# Generate a random token for the session
def generate_token():
    return secrets.token_urlsafe(32)

# Set session with expiration
def set_session_cookie(response, token, expires_in_seconds):
    expires = datetime.datetime.now() + datetime.timedelta(seconds=expires_in_seconds)
    response.set_cookie('session_token', token, expires=expires)

# Check if session is expired
def is_logged_in(request):
    token = request.cookies.get('session_token')
    if token:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE session_token = ?', (token,)).fetchone()
        conn.close()
        
        if user and datetime.datetime.now() < user['expires']:
            return user
        else:
            return None

# Login endpoint
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
  
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
  
    if user and user['password'] == password:
        token = generate_token()
        conn = get_db_connection()
        expires = datetime.datetime.now() + datetime.timedelta(seconds=60)
        conn.execute('UPDATE users SET session_token = ?, expires = ? WHERE id = ?', (token, expires, user['id']))
        conn.commit()
  
        # Fetch the updated user record to ensure expires is populated
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone()
        conn.close()
  
        response = make_response(jsonify({'message': 'Login successful'}))
        set_session_cookie(response, token, 3600)
        return response
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/set_cookie')
def set_cookie():
    response = make_response("Setting a test cookie")
    response.set_cookie('test_cookie', 'test_value', httponly=True)
    return response

# Protected endpoint (requires login)
@app.route('/protected', methods=['GET'])
def protected():
    user = is_logged_in(request)
    if user:
        return jsonify({'message': 'You are logged in as: ' + user['username']})
    else:
        return jsonify({'error': 'You are not logged in'}), 401

if __name__ == '__main__':
    init_db()
    app.run(debug=True)