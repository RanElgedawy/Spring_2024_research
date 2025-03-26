import sqlite3
import bcrypt

DATABASE_NAME = 'ecommerce.db'

def connect_db():
    """Connects to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def create_users_table():
    """Creates the 'users' table if it doesn't exist."""
    conn = connect_db()
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
    """Registers a new user."""
    conn = connect_db()
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return "Username already exists."

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert the new user into the database
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return "User registered successfully."
    except sqlite3.Error as e:
        conn.close()
        return f"Error during registration: {e}"

def login_user(username, password):
    """Logs in an existing user."""
    conn = connect_db()
    cursor = conn.cursor()

    # Retrieve the user from the database
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        # Verify the password
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return "Login successful."
        else:
            return "Incorrect password."
    else:
        return "User not found."

def test_registration_and_login():
    """Tests the user registration and login functionality."""
    create_users_table()  # Ensure the table exists

    print("--- User Registration ---")
    registration_result1 = register_user("testuser1", "password123")
    print(f"Registration attempt 1: {registration_result1}")

    registration_result2 = register_user("testuser1", "anotherpassword")
    print(f"Registration attempt 2 (same username): {registration_result2}")

    registration_result3 = register_user("newuser", "securepassword")
    print(f"Registration attempt 3: {registration_result3}")

    print("\n--- User Login ---")
    login_result1 = login_user("testuser1", "password123")
    print(f"Login attempt 1 (correct credentials): {login_result1}")

    login_result2 = login_user("testuser1", "wrongpassword")
    print(f"Login attempt 2 (incorrect password): {login_result2}")

    login_result3 = login_user("nonexistentuser", "anypassword")
    print(f"Login attempt 3 (user not found): {login_result3}")

    login_result4 = login_user("newuser", "securepassword")
    print(f"Login attempt 4 (new user login): {login_result4}")

if __name__ == "__main__":
    # You might need to install the 'bcrypt' library if you don't have it.
    # You can install it using pip: pip install bcrypt
    try:
        import bcrypt
        test_registration_and_login()
    except ImportError:
        print("Error: The 'bcrypt' library is not installed.")
        print("Please install it using: pip install bcrypt")