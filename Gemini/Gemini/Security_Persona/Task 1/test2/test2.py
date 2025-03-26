import hashlib
import sqlite3

def create_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def register_user(username, password):
    if not username or not password:
        raise ValueError("Username and password are required.")
    
    # Check if user already exists
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close() 

    if result:
        raise ValueError("User already exists.")
    hashed_password = hash_password(password)
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()

def login_user(username, password):
    if not username or not password:
        raise ValueError("Username and password are required.")

        # Check if user exists
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close() 

    if not result:
        raise ValueError("User not found.")
    
    hashed_password = hash_password(password)
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, hashed_password))
    result = c.fetchone()
    conn.close()
    return result is not None

# Create the database if it doesn't exist
create_database()

# Test the registration and login functionality
username = "test"
password = "testpassword"

# Register the user
# register_user(username, password)

# Log in the user
if login_user(username, password):
    print("Login successful!")
else:
    print("Login failed.")