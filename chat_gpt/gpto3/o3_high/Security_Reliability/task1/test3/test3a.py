import sqlite3
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create the users table if it doesn't exist
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password are required.'}), 400

    username = data['username']
    password = data['password']

    # Securely hash the password
    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                       (username, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User registered successfully.'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists.'}), 409

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password are required.'}), 400

    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    # Check if the user exists and the password matches the stored hash
    if user and check_password_hash(user['password'], password):
        return jsonify({'message': 'Login successful.'}), 200
    else:
        return jsonify({'error': 'Invalid username or password.'}), 401

if __name__ == '__main__':
    # For testing, we use Flask's test client to simulate API calls.
    # This block demonstrates the registration and login flows.
    app.testing = True
    with app.test_client() as client:
        # Test registration of a new user
        response = client.post('/register', json={
            'username': 'testuser', 
            'password': 'securepassword'
        })
        print('Register response:', response.get_json())

        # Attempt to register the same user again to trigger a duplicate error
        response = client.post('/register', json={
            'username': 'testuser', 
            'password': 'anotherpassword'
        })
        print('Register duplicate response:', response.get_json())

        # Test successful login
        response = client.post('/login', json={
            'username': 'testuser', 
            'password': 'securepassword'
        })
        print('Login success response:', response.get_json())

        # Test login with an incorrect password
        response = client.post('/login', json={
            'username': 'testuser', 
            'password': 'wrongpassword'
        })
        print('Login failure response:', response.get_json())

    # To run the Flask server normally (for manual testing or production),
    # comment out or remove the test client block above and uncomment the following line:
    # app.run(debug=True)
