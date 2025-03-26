import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize the database and create the 'users' table if it doesn't exist.
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Register a new user by hashing the password and storing the username and hash.
def register_user(username, password):
    password_hash = generate_password_hash(password)
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        print(f"User '{username}' registered successfully.")
    except sqlite3.IntegrityError:
        print("Error: Username already exists.")
    conn.close()

# Attempt to login by checking the given password against the stored hash.
def login_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        print("Error: Username not found.")
        return False
    stored_hash = row[0]
    if check_password_hash(stored_hash, password):
        print("Login successful!")
        return True
    else:
        print("Error: Invalid password.")
        return False

# Simple test function to demonstrate registration and login.
def test():
    print("Initializing database...")
    init_db()
    
    # Register a test user
    username = "testuser"
    password = "TestPass123"
    print(f"\nRegistering user '{username}' with password '{password}'...")
    register_user(username, password)
    
    # Attempt to login with the correct credentials
    print(f"\nAttempting to login as '{username}' with the correct password...")
    login_user(username, password)
    
    # Attempt to login with an incorrect password
    print(f"\nAttempting to login as '{username}' with an incorrect password...")
    login_user(username, "WrongPass")

if __name__ == '__main__':
    test()
