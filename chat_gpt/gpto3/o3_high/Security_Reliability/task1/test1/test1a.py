import sqlite3
import hashlib
import os
import binascii

# --- Configuration ---
DB_FILE = "users.db"
HASH_NAME = 'sha256'
ITERATIONS = 100_000
SALT_SIZE = 16

# --- Database Setup ---
def create_connection(db_file=DB_FILE):
    """Create and return a database connection."""
    return sqlite3.connect(db_file)

def create_table(conn):
    """Create the users table if it does not exist."""
    with conn:
        conn.execute("DROP TABLE IF EXISTS users")
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)

# --- Password Hashing ---
def hash_password(password: str) -> str:
    """Generate a salted hash for the given password."""
    salt = os.urandom(SALT_SIZE)
    pwdhash = hashlib.pbkdf2_hmac(HASH_NAME, password.encode('utf-8'), salt, ITERATIONS)
    salt_hex = binascii.hexlify(salt).decode('ascii')
    hash_hex = binascii.hexlify(pwdhash).decode('ascii')
    # Format: salt$hash
    return f"{salt_hex}${hash_hex}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against one provided by user."""
    try:
        salt_hex, hash_hex = stored_password.split('$')
    except ValueError:
        return False
    salt = binascii.unhexlify(salt_hex.encode('ascii'))
    pwdhash = hashlib.pbkdf2_hmac(HASH_NAME, provided_password.encode('utf-8'), salt, ITERATIONS)
    return binascii.hexlify(pwdhash).decode('ascii') == hash_hex

# --- User Registration and Login ---
def register_user(conn, username: str, password: str):
    """Register a new user by inserting their credentials into the DB."""
    password_hash = hash_password(password)
    try:
        with conn:
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                         (username, password_hash))
        print(f"User '{username}' registered successfully.")
    except sqlite3.IntegrityError:
        print(f"Error: The username '{username}' is already taken.")

def login_user(conn, username: str, password: str):
    """Attempt to log in a user by verifying their credentials."""
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if row is None:
        print("Login failed: user not found.")
        return False
    stored_password = row[0]
    if verify_password(stored_password, password):
        print("Login successful!")
        return True
    else:
        print("Login failed: incorrect password.")
        return False

# --- Testing Functionality ---
def test_functionality(conn):
    """Run some simple tests to verify registration and login."""
    print("Running tests...")
    test_username = "testuser"
    test_password = "TestPassword123!"

    # Clean up any previous test run
    conn.execute("DELETE FROM users WHERE username = ?", (test_username,))
    conn.commit()

    # Register the test user
    register_user(conn, test_username, test_password)

    # Test login with the correct password
    assert login_user(conn, test_username, test_password) == True, "Test failed: correct credentials should log in."
    
    # Test login with an incorrect password
    assert login_user(conn, test_username, "WrongPassword") == False, "Test failed: incorrect password should not log in."
    
    # Try registering the same user again to test uniqueness constraint
    register_user(conn, test_username, test_password)
    
    print("All tests passed.\n")

# --- Main Interactive Menu ---
def main():
    conn = create_connection()
    create_table(conn)
    
    # Run tests automatically on startup
    test_functionality(conn)
    
    # Interactive loop for registration and login
    while True:
        print("Select an option:")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == '1':
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            register_user(conn, username, password)
        elif choice == '2':
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            login_user(conn, username, password)
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
