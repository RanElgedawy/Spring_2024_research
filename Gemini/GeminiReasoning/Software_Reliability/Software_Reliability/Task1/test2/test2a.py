import sqlite3
import bcrypt

DATABASE_NAME = 'ecommerce.db'

def connect_db():
    """Connects to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # To access columns by name
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

def register_user(username, password):
    """Registers a new user."""
    conn = connect_db()
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return False, "Username already exists."

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return True, "User registered successfully."
    except sqlite3.Error as e:
        conn.close()
        return False, f"Error during registration: {e}"

def login_user(username, password):
    """Logs in an existing user."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return True, "Login successful."
        else:
            return False, "Incorrect password."
    else:
        return False, "User not found."

def test_registration_and_login():
    """Provides a way to test the registration and login functionality."""
    create_users_table()  # Ensure the table exists

    while True:
        print("\nChoose an action:")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Enter username for registration: ")
            password = input("Enter password for registration: ")
            success, message = register_user(username, password)
            print(message)
        elif choice == '2':
            username = input("Enter username for login: ")
            password = input("Enter password for login: ")
            success, message = login_user(username, password)
            print(message)
        elif choice == '3':
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    # This block will only run when the script is executed directly
    test_registration_and_login()