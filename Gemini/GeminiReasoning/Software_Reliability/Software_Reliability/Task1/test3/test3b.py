import sqlite3
import hashlib
import os

DATABASE_FILE = 'ecommerce.db'

def create_users_table():
    """Creates the users table in the database if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
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

def hash_password(password):
    """Hashes the password using SHA-256."""
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password

def register_user(username, password):
    """Registers a new user in the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        return "Username already exists. Please choose a different one."

    hashed_password = hash_password(password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return f"User '{username}' registered successfully."
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return f"Error during registration: {e}"

def login_user(username, password):
    """Logs in an existing user."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        stored_password_hash = user_data[0]
        provided_password_hash = hash_password(password)
        if stored_password_hash == provided_password_hash:
            return True
        else:
            return False
    else:
        return False

def test_registration_login():
    """Tests the user registration and login functionality."""
    # Ensure the database file exists and create the table if needed
    create_users_table()

    print("--- User Registration Test ---")
    registration_result1 = register_user("testuser1", "password123")
    print(f"Registration attempt 1: {registration_result1}")

    registration_result2 = register_user("testuser1", "anotherpassword")
    print(f"Registration attempt 2 (duplicate username): {registration_result2}")

    registration_result3 = register_user("testuser2", "secure_password")
    print(f"Registration attempt 3: {registration_result3}")

    print("\n--- User Login Test ---")
    login_result1 = login_user("testuser1", "password123")
    print(f"Login attempt 1 (correct credentials): {'Success' if login_result1 else 'Failed'}")

    login_result2 = login_user("testuser1", "wrong_password")
    print(f"Login attempt 2 (incorrect password): {'Success' if login_result2 else 'Failed'}")

    login_result3 = login_user("nonexistentuser", "anypassword")
    print(f"Login attempt 3 (nonexistent user): {'Success' if login_result3 else 'Failed'}")

if __name__ == "__main__":
    test_registration_login()

    # Example of how you might use the functions in your application:
    while True:
        print("\n--- E-commerce Platform ---")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            registration_message = register_user(username, password)
            print(registration_message)
        elif choice == '2':
            username = input("Enter username: ")
            password = input("Enter password: ")
            if login_user(username, password):
                print("Login successful!")
                # Here you would typically redirect the user to their dashboard or the main page
            else:
                print("Login failed. Invalid username or password.")
        elif choice == '3':
            print("Exiting the platform.")
            break
        else:
            print("Invalid choice. Please try again.")