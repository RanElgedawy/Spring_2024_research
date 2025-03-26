import sqlite3
import bcrypt

class UserAuth:
    def __init__(self, db_name="users.db"):
        self.db_name = db_name
        self.conn = self._create_connection()
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_connection(self):
        """Creates a database connection."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            return conn
        except sqlite3.Error as e:
            print(e)
        return conn

    def _create_table(self):
        """Creates the users table if it doesn't exist."""
        try:
            self.cursor.execute("DROP TABLE IF EXISTS users")
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def register_user(self, username, password):
        """Registers a new user."""
        if not username:
            print("Username cannot be empty.")
            return False
        if not password:
            print("Password cannot be empty.")
            return False

        if self._get_user(username):
            print(f"Username '{username}' already exists.")
            return False

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            self.cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
            self.conn.commit()
            print(f"User '{username}' registered successfully.")
            return True
        except sqlite3.Error as e:
            print(e)
            return False

    def login_user(self, username, password):
        """Logs in an existing user."""
        if not username:
            print("Username cannot be empty.")
            return False
        if not password:
            print("Password cannot be empty.")
            return False

        user = self._get_user(username)
        if user:
            stored_password_hash = user[2]
            if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                print(f"User '{username}' logged in successfully.")
                return True
            else:
                print("Incorrect password.")
                return False
        else:
            print(f"User '{username}' not found.")
            return False

    def _get_user(self, username):
        """Retrieves a user from the database by username."""
        self.cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        return self.cursor.fetchone()

    def close_connection(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

# --- Testing the functionality ---
if __name__ == "__main__":
    auth_system = UserAuth()

    print("--- Registration Attempts ---")
    auth_system.register_user("", "P@$$wOrd123") # Empty username
    auth_system.register_user("testuser", "") # Empty password
    auth_system.register_user("validuser", "SecurePassword") # Valid registration
    auth_system.register_user("validuser", "AnotherPassword") # Try to register with the same username

    print("\n--- Login Attempts ---")
    auth_system.login_user("", "P@$$wOrd123") # Empty username
    auth_system.login_user("testuser", "") # Empty password
    auth_system.login_user("validuser", "SecurePassword") # Correct credentials
    auth_system.login_user("validuser", "WrongPassword") # Incorrect password
    auth_system.login_user("nonexistentuser", "AnyPassword") # Non-existent user

    auth_system.close_connection()