import sqlite3
import bcrypt

# Database setup
def create_tables():
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    ''')
    
    connection.commit()
    connection.close()

# Register a new user
def register_user(username, password):
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        # Insert user into database
        cursor.execute('''
        INSERT INTO users (username, password) VALUES (?, ?)
        ''', (username, hashed_password))
        
        connection.commit()
        print(f"User {username} registered successfully.")
    except sqlite3.IntegrityError:
        print(f"Error: Username {username} already exists.")
    
    connection.close()

# Verify user login
def login_user(username, password):
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    
    # Retrieve the user's hashed password from the database
    cursor.execute('''
    SELECT password FROM users WHERE username = ?
    ''', (username,))
    result = cursor.fetchone()
    
    connection.close()
    
    if result is None:
        print(f"Error: User {username} not found.")
        return False
    
    stored_password = result[0]
    
    # Check if the provided password matches the stored hashed password
    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
        print(f"User {username} logged in successfully.")
        return True
    else:
        print(f"Error: Incorrect password for {username}.")
        return False

# Test the functionality
def test():
    # Create the database and tables
    create_tables()

    # Register new users
    print("\n-- Registering Users --")
    register_user("alice", "password123")
    register_user("bob", "securepassword456")
    register_user("alice", "duplicate_username")  # This should fail

    # Attempt to log in users
    print("\n-- Logging in Users --")
    login_user("alice", "password123")    # Success
    login_user("bob", "wrongpassword")    # Incorrect password
    login_user("charlie", "noaccount")    # User not found

if __name__ == "__main__":
    test()
