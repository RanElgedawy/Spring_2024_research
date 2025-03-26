import sqlite3
import os
import hashlib
import hmac

# Constants for password hashing
HASH_NAME = 'sha256'
ITERATIONS = 100_000
SALT_SIZE = 16  # 16 bytes salt

DB_NAME = "users.db"

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    return conn

def create_users_table():
    """Create the users table if it doesn't exist."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            salt BLOB NOT NULL,
            password_hash BLOB NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password: str, salt: bytes) -> bytes:
    """Generate a password hash using PBKDF2-HMAC."""
    return hashlib.pbkdf2_hmac(HASH_NAME, password.encode('utf-8'), salt, ITERATIONS)

def register_user(username: str, password: str) -> bool:
    """Register a new user with a hashed password."""
    salt = os.urandom(SALT_SIZE)
    password_hash = hash_password(password, salt)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)",
                    (username, salt, password_hash))
        conn.commit()
        print(f"User '{username}' registered successfully.")
        return True
    except sqlite3.IntegrityError:
        print(f"Error: Username '{username}' is already taken.")
        return False
    finally:
        conn.close()

def verify_password(stored_hash: bytes, salt: bytes, provided_password: str) -> bool:
    """Verify a stored password against one provided by user."""
    provided_hash = hash_password(provided_password, salt)
    return hmac.compare_digest(stored_hash, provided_hash)

def login_user(username: str, password: str) -> bool:
    """Attempt to log a user in by verifying their password."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT salt, password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        print(f"Login failed: Username '{username}' not found.")
        return False
    salt, stored_hash = row
    if verify_password(stored_hash, salt, password):
        print(f"Login successful for user '{username}'.")
        return True
    else:
        print(f"Login failed: Incorrect password for user '{username}'.")
        return False

def run_tests():
    """Test the registration and login functionality."""
    # First, create the database and table
    create_users_table()
    
    # Test user registration
    username = "alice"
    password = "securePa$$w0rd"
    print("Registering user...")
    if register_user(username, password):
        print("Testing login with correct password...")
        login_user(username, password)
        
        print("Testing login with incorrect password...")
        login_user(username, "wrongPassword")
    else:
        print("Registration failed. User may already exist.")

if __name__ == "__main__":
    run_tests()
