import hashlib
import sqlite3
import random
import string

def create_database_and_tables():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password_hash TEXT NOT NULL,
                 salt TEXT NOT NULL
                 )''')

    conn.commit()
    conn.close()

def generate_salt(length=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def hash_password(password, salt):
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def register_user(username, password):
    salt = generate_salt()
    hashed_password = hash_password(password, salt)

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
              (username, hashed_password, salt))

    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute("SELECT password_hash, salt FROM users WHERE username = ?", (username,))
    result = c.fetchone()

    if result is None:
        return False

    stored_password_hash, stored_salt = result
    hashed_input_password = hash_password(password, stored_salt)

    if hashed_input_password == stored_password_hash:
        return True
    else:
        return False

# Create the database and tables if they don't exist
create_database_and_tables()

# Example usage:
if register_user("john_doe", "mystrongpassword"):
    print("Registration successful!")
else:
    print("Registration failed.")

if login_user("john_doe", "mystrongpassword"):
    print("Login successful!")
else:
    print("Login failed.")