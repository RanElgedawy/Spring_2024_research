import sqlite3
import bcrypt

DATABASE_NAME = 'ecommerce.db'

def create_users_table():
    """Creates the users table in the database if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Users table created (if it didn't exist).")

def register_user(username, password, email=None):
    """Registers a new user in the database."""
    if not username or not password:
        return "Error: Username and password are required."

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return "Error: Username already exists."

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert the new user into the database
    try:
        cursor.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                       (username, hashed_password, email))
        conn.commit()
        conn.close()
        return f"User '{username}' registered successfully."
    except sqlite3.Error as e:
        conn.close()
        return f"Error during registration: {e}"

def login_user(username, password):
    """Logs in an existing user."""
    if not username or not password:
        return None, "Error: Username and password are required."

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Retrieve the user from the database
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        user_id, db_username, hashed_password = user_data
        # Verify the password
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            return {"id": user_id, "username": db_username}, "Login successful."
        else:
            return None, "Error: Incorrect password."
    else:
        return None, "Error: User not found."

def test_registration_login():
    """Tests the user registration and login functionality."""
    print("\n--- Testing User Registration ---")
    registration_result1 = register_user("testuser1", "password123", "test1@example.com")
    print(f"Registration 1: {registration_result1}")
    registration_result2 = register_user("testuser2", "secure_pass", "test2@example.com")
    print(f"Registration 2: {registration_result2}")
    registration_result3 = register_user("testuser1", "another_pass")  # Try to register with the same username
    print(f"Registration 3: {registration_result3}")
    registration_result4 = register_user("", "some_password")  # Missing username
    print(f"Registration 4: {registration_result4}")
    registration_result5 = register_user("another_user", "")  # Missing password
    print(f"Registration 5: {registration_result5}")
    registration_result6 = register_user(None, "test") # Null username
    print(f"Registration 6: {registration_result6}")
    registration_result7 = register_user("test", None) # Null password
    print(f"Registration 7: {registration_result7}")

    print("\n--- Testing User Login ---")
    login_result1, login_message1 = login_user("testuser1", "password123")
    print(f"Login 1: {login_message1}, User Data: {login_result1}")
    login_result2, login_message2 = login_user("testuser1", "wrong_password")
    print(f"Login 2: {login_message2}, User Data: {login_result2}")
    login_result3, login_message3 = login_user("nonexistentuser", "any_password")
    print(f"Login 3: {login_message3}, User Data: {login_result3}")
    login_result4, login_message4 = login_user("testuser2", "secure_pass")
    print(f"Login 4: {login_message4}, User Data: {login_result4}")
    login_result5, login_message5 = login_user("", "password") # Missing username
    print(f"Login 5: {login_message5}, User Data: {login_result5}")
    login_result6, login_message6 = login_user("some_user", "") # Missing password
    print(f"Login 6: {login_message6}, User Data: {login_result6}")
    login_result7, login_message7 = login_user(None, "test") # Null username
    print(f"Login 7: {login_message7}, User Data: {login_result7}")
    login_result8, login_message8 = login_user("test", None) # Null password
    print(f"Login 8: {login_message8}, User Data: {login_result8}")

if __name__ == "__main__":
    # Ensure the users table exists
    create_users_table()

    # Run the tests
    test_registration_login()

    print("\n--- Manual Registration and Login Example ---")
    while True:
        action = input("Choose an action (register/login/exit): ").lower()
        if action == 'register':
            username = input("Enter username: ")
            password = input("Enter password: ")
            email = input("Enter email (optional): ")
            result = register_user(username, password, email)
            print(result)
        elif action == 'login':
            username = input("Enter username: ")
            password = input("Enter password: ")
            user, message = login_user(username, password)
            print(message)
            if user:
                print(f"Logged in as user ID: {user['id']}, Username: {user['username']}")
        elif action == 'exit':
            break
        else:
            print("Invalid action. Please choose 'register', 'login', or 'exit'.")