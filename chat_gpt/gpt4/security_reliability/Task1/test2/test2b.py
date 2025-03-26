import sqlite3
import bcrypt

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('ecommerce_users.db')
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
''')
conn.commit()

def hash_password(password):
    """Hash a plaintext password using bcrypt."""
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash

def register_user(username, password):
    """Register a new user with a hashed password."""
    try:
        # Hash the user's password
        password_hash = hash_password(password)
        # Insert user into the database
        cursor.execute('''
        INSERT INTO users (username, password_hash) VALUES (?, ?)
        ''', (username, password_hash))
        conn.commit()
        print(f"User {username} registered successfully!")
    except sqlite3.IntegrityError:
        print(f"Username {username} is already taken.")

def verify_password(stored_password_hash, password):
    """Check if a plaintext password matches the stored hashed password."""
    return bcrypt.checkpw(password.encode('utf-8'), stored_password_hash)

def login_user(username, password):
    """Allow a user to log in by verifying their credentials."""
    # Fetch the user's hashed password from the database
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    
    if result is None:
        print("User not found!")
        return False
    
    stored_password_hash = result[0]
    
    if verify_password(stored_password_hash, password):
        print(f"User {username} logged in successfully!")
        return True
    else:
        print("Invalid credentials.")
        return False

# Test the registration and login functionality
def test():
    print("\n### Registration and Login Test ###")
    # Register a new user
    register_user("test_user", "secure_password")
    
    # Try to log in with the correct password
    login_user("test_user", "secure_password")
    
    # Try to log in with an incorrect password
    login_user("test_user", "wrong_password")

# Uncomment to run the test function
test()

# Close the database connection when done
conn.close()