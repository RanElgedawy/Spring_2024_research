import sqlite3
import hashlib
import secrets

def create_database():
    """Creates the necessary database tables."""
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def register_user(username, password, email):
    """Registers a new user."""
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Hash the password for security
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    try:
        cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                       (username, hashed_password, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Handle duplicate username or email
        return False
    finally:
        conn.close()

def login_user(username, password):
    """Logs in a user."""
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result and hashlib.sha256(password.encode('utf-8')).hexdigest() == result[0]:
            return True
        else:
            return False
    finally:
        conn.close()

# Test the functions
if __name__ == "__main__":
    create_database()

    # Register a new user
    if register_user("john_doe", "password123", "johndoe@example.com"):
        print("User registered successfully.")
    else:
        print("Registration failed (duplicate username or email).")

    # Log in the user
    if login_user("john_doe", "password123"):
        print("Login successful.")
    else:
        print("Login failed.")