from flask import Flask, request, jsonify, session, render_template_string
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Create the users table if it does not exist
    conn = get_db_connection()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        ''')
    conn.close()

# Initialize the database on startup
init_db()

@app.route('/')
def home():
    return 'Welcome to the E-commerce Platform'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get data from the registration form
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        # Basic validation
        if not username or not password or not email:
            return jsonify({'error': 'Missing fields'}), 400
        
        try:
            conn = get_db_connection()
            with conn:
                conn.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                             (username, password, email))
            conn.close()
            return jsonify({'message': 'User registered successfully'})
        except sqlite3.IntegrityError as e:
            # Handle duplicate entries for username or email
            return jsonify({'error': 'User already exists or email is taken'}), 400
    else:
        # Render a simple HTML registration form
        return render_template_string('''
        <h2>Register</h2>
        <form method="post">
          Username: <input type="text" name="username"><br>
          Email: <input type="email" name="email"><br>
          Password: <input type="password" name="password"><br>
          <input type="submit" value="Register">
        </form>
        ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get login credentials
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Missing fields'}), 400
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            return jsonify({'message': 'Login successful'})
        else:
            return jsonify({'error': 'Invalid credentials'}), 400
    else:
        # Render a simple HTML login form
        return render_template_string('''
        <h2>Login</h2>
        <form method="post">
          Username: <input type="text" name="username"><br>
          Password: <input type="password" name="password"><br>
          <input type="submit" value="Login">
        </form>
        ''')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'})

# Test endpoint to demonstrate registration and login functionality using Flask's test client.
@app.route('/test')
def test():
    with app.test_client() as client:
        # Register a test user
        reg_response = client.post('/register', data={
            'username': 'testuser',
            'password': 'testpass',
            'email': 'test@example.com'
        })
        # Attempt to log in with the test user
        login_response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        })
        return jsonify({
            'register': reg_response.get_json(),
            'login': login_response.get_json()
        })

if __name__ == '__main__':
    app.run(debug=True)
