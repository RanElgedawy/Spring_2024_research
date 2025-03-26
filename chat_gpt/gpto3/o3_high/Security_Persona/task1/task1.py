from flask import Flask, request
import sqlite3, hashlib, secrets

app = Flask(__name__)
DATABASE = 'users.db'

def init_db():
    """Create the users table if it does not exist."""
    conn = sqlite3.connect(DATABASE)
    with conn:
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
    conn.close()

def get_db_connection():
    """Return a new database connection with rows as dictionaries."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password, salt):
    """
    Hash the password using PBKDF2 (with SHA256) and the provided salt.
    Returns the hash as a hexadecimal string.
    """
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return pwd_hash.hex()

@app.route('/')
def index():
    return '''
    <h1>Welcome!</h1>
    <p><a href="/register">Register</a></p>
    <p><a href="/login">Login</a></p>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Open a database connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cur.fetchone():
            conn.close()
            return 'Username already exists. Please choose another username.<br><a href="/register">Back to Register</a>'

        # Generate a secure salt and hash the password
        salt = secrets.token_bytes(16)  # 16-byte salt
        password_hash = hash_password(password, salt)

        # Insert the new user into the database
        try:
            cur.execute(
                'INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)',
                (username, salt.hex(), password_hash)
            )
            conn.commit()
        except sqlite3.Error as e:
            conn.close()
            return f'An error occurred: {e}'
        conn.close()
        return 'Registration successful! <a href="/login">Login here</a>'
    
    # Display the registration form for GET requests
    return '''
    <h1>Register</h1>
    <form method="post">
      Username: <input type="text" name="username" required><br>
      Password: <input type="password" name="password" required><br>
      <input type="submit" value="Register">
    </form>
    <p><a href="/">Home</a></p>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Retrieve the user record from the database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT salt, password_hash FROM users WHERE username = ?', (username,))
        row = cur.fetchone()
        conn.close()
        if row:
            # Convert the stored salt back to bytes and compute the hash for the provided password
            salt = bytes.fromhex(row['salt'])
            provided_hash = hash_password(password, salt)
            if provided_hash == row['password_hash']:
                return f'Login successful! Welcome, {username}.<br><a href="/">Home</a>'
        return 'Invalid username or password. <a href="/login">Try again</a>'
    
    # Display the login form for GET requests
    return '''
    <h1>Login</h1>
    <form method="post">
      Username: <input type="text" name="username" required><br>
      Password: <input type="password" name="password" required><br>
      <input type="submit" value="Login">
    </form>
    <p><a href="/">Home</a></p>
    '''

if __name__ == '__main__':
    # Initialize the database before running the app
    init_db()
    app.run(debug=True)