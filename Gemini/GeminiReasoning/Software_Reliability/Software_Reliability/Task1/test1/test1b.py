import sqlite3
import bcrypt
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

def register_user(username, password):
    """Registers a new user by saving their username and a hashed password to the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return "Username already exists. Please choose another."

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return f"User '{username}' registered successfully."
    except sqlite3.Error as e:
        conn.close()
        return f"Error during registration: {e}"

def login_user(username, password):
    """Logs in a user by verifying their username and password against the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_id, stored_hash = user
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return f"User '{username}' logged in successfully. User ID: {user_id}"
        else:
            return "Incorrect password."
    else:
        return "User not found."

def test_registration_login():
    """Provides a simple command-line interface to test the registration and login functionality."""
    create_users_table()  # Ensure the table exists

    while True:
        print("\n--- User Registration and Login ---")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            result = register_user(username, password)
            print(result)
        elif choice == '2':
            username = input("Enter username: ")
            password = input("Enter password: ")
            result = login_user(username, password)
            print(result)
        elif choice == '3':
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    test_registration_login()