import hashlib
import sqlite3

def create_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password_hash TEXT NOT NULL
                 )''')

    conn.commit()
    conn.close()

def hash_password(password):
    salt = "your_unique_salt"  # Replace with a strong, randomly generated salt
    hashed_password = hashlib.sha256(f"{password}{salt}".encode('utf-8')).hexdigest()
    return hashed_password

def register_user(username, password):
    hashed_password = hash_password(password)

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()

def login_user(username, password):
    hashed_password = hash_password(password)

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, hashed_password))
    user = c.fetchone()
    conn.close()

    if user:
        return True
    else:
        return False

# Create the database if it doesn't exist
create_database()

# Test registration and login
register_user("john_doe", "my_strong_password")
if login_user("john_doe", "my_strong_password"):
    print("Login successful!")
else:
    print("Login failed.")