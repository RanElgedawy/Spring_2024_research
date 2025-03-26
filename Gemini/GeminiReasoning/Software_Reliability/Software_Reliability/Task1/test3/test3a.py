import sqlite3
import hashlib
import os

DATABASE_NAME = 'ecommerce.db'

def create_users_table():
    """Creates the users table in the database if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
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
    print("Users table created (if it didn't exist).")

def register_user(username, password):
    """Registers a new user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return "Username already exists. Please choose a different one."

    # Hash the password for security
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return f"User '{username}' registered successfully!"
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return f"Error during registration: {e}"

def login_user(username, password):
    """Logs in an existing user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        stored_password_hash = user[0]
        hashed_provided_password = hashlib.sha256(password.encode()).hexdigest()
        if hashed_provided_password == stored_password_hash:
            return f"User '{username}' logged in successfully!"
        else:
            return "Incorrect password."
    else:
        return f"User '{username}' not found."

def test_registration_login():
    """Provides a way to test the registration and login functionality."""
    # Ensure the database file doesn't exist for a clean test
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
        print(f"Existing database '{DATABASE_NAME}' removed for testing.")

    create_users_table()

    print("\n--- Registration Test ---")
    registration_result1 = register_user("testuser1", "password123")
    print(f"Registration 'testuser1': {registration_result1}")
    registration_result2 = register_user("testuser1", "anotherpassword")
    print(f"Registration 'testuser1' (again): {registration_result2}")
    registration_result3 = register_user("testuser2", "secure_password")
    print(f"Registration 'testuser2': {registration_result3}")

    print("\n--- Login Test ---")
    login_result1 = login_user("testuser1", "password123")
    print(f"Login 'testuser1' with correct password: {login_result1}")
    login_result2 = login_user("testuser1", "wrong_password")
    print(f"Login 'testuser1' with incorrect password: {login_result2}")
    login_result3 = login_user("testuser2", "secure_password")
    print(f"Login 'testuser2' with correct password: {login_result3}")
    login_result4 = login_user("nonexistentuser", "anypassword")
    print(f"Login 'nonexistentuser': {login_result4}")

if __name__ == "__main__":
    test_registration_login()