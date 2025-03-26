import sqlite3
import bcrypt
import os

DATABASE_NAME = 'ecommerce.db'

def connect_db():
    """Connects to the database and returns the connection object."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def create_users_table():
    """Creates the users table if it doesn't exist."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("Users table created (if it didn't exist).")

def register_user(username, password):
    """Registers a new user by saving their username and a hashed password."""
    conn = connect_db()
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return "Error: Username already exists."

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                       (username, hashed_password.decode('utf-8')))
        conn.commit()
        conn.close()
        return f"User '{username}' registered successfully."
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return f"Error during registration: {e}"

def login_user(username, password):
    """Logs in a user by verifying their username and password."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return f"User '{username}' logged in successfully."
        else:
            return "Error: Incorrect password."
    else:
        return "Error: User not found."

def test_registration_login():
    """Provides a simple command-line interface to test the functionality."""
    create_users_table()  # Ensure the table exists

    while True:
        print("\nChoose an action:")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter your choice (1/2/3): ")

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
    # Check if bcrypt is installed
    try:
        import bcrypt
    except ImportError:
        print("Error: The 'bcrypt' library is not installed.")
        print("Please install it using: pip install bcrypt")
        exit()

    test_registration_login()