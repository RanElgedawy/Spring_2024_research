import hashlib
import sqlite3
import flask

app = flask.Flask(__name__)

# Database configuration
DATABASE_URL = 'your_database_url'  # Replace with your actual database URL

# Create database and tables if they don't exist
def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password_hash TEXT NOT NULL
                 )''')
    conn.commit()
    conn.close()

# Hash password using a strong algorithm (e.g., bcrypt)
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Register a new user
@app.route('/register', methods=['POST'])
def register():
    username = flask.request.form['username']
    password = flask.request.form['password']
    password_hash = hash_password(password)

    conn = sqlite3.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
    conn.commit()
    conn.close()

    return "User registered successfully!"

# Login a user
@app.route('/login', methods=['POST'])
def login():
    username = flask.request.form['username']
    password = flask.request.form['password']

    conn = sqlite3.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()

    if result and hashlib.sha256(password.encode('utf-8')).hexdigest() == result[0]:
        # Successful login
        return "Login successful!"
    else:
        # Login failed
        return "Invalid username or password"

if __name__ == '__main__':
    init_db()
    app.run(debug=True)