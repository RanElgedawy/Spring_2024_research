import sqlite3
import bcrypt

# Database setup function
def setup_database():
    conn = sqlite3.connect('ecommerce_users.db')
    cursor = conn.cursor()

    # Create users table if it doesn't exist
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

# Registration function
def register_user(username, password):
    conn = sqlite3.connect('ecommerce_users.db')
    cursor = conn.cursor()

    # Check if username already exists
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        print("Username already exists. Please choose a different username.")
        conn.close()
        return False

    # Hash the password using bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Insert the user into the database
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    
    conn.commit()
    conn.close()
    print(f"User {username} registered successfully.")
    return True

# Login function
def login_user(username, password):
    conn = sqlite3.connect('ecommerce_users.db')
    cursor = conn.cursor()

    # Fetch the user's hashed password from the database
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()

    if result is None:
        print("Username does not exist.")
        conn.close()
        return False

    hashed_password = result[0]

    # Check if the password matches the hashed password
    if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
        print(f"Login successful. Welcome {username}!")
        conn.close()
        return True
    else:
        print("Incorrect password.")
        conn.close()
        return False

# Test functionality
def test():
    # Automatically create tables in the DB
    setup_database()

    # Test registration
    print("Testing registration...")
    register_user("test_user", "secure_password123")

    # Test login with correct credentials
    print("\nTesting login with correct credentials...")
    login_user("test_user", "secure_password123")

    # Test login with incorrect credentials
    print("\nTesting login with incorrect credentials...")
    login_user("test_user", "wrong_password")

# Run the test
if __name__ == "__main__":
    test()