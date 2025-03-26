import sqlite3
import bcrypt
from getpass import getpass

class AuthSystem:
    def __init__(self, db_name='users.db'):
        self.db_name = db_name
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            conn.execute("DROP TABLE IF EXISTS users")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            ''')
            conn.commit()

    def _get_db_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_name)

    def register_user(self):
        """Register a new user with password hashing"""
        username = input("Enter username: ").strip()
        password = getpass("Enter password: ").strip()

        if not username or not password:
            print("Username and password are required")
            return

        # Generate salt and hash password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password_hash)
                    VALUES (?, ?)
                ''', (username, password_hash))
                conn.commit()
                print("Registration successful!")
        except sqlite3.IntegrityError:
            print("Username already exists")

    def login_user(self):
        """Authenticate user with password verification"""
        username = input("Enter username: ").strip()
        password = getpass("Enter password: ").strip()

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT password_hash FROM users WHERE username = ?
            ''', (username,))
            result = cursor.fetchone()

        if not result:
            print("User not found")
            return False

        stored_hash = result[0]
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            print("Login successful!")
            return True
        else:
            print("Invalid password")
            return False

def main():
    auth = AuthSystem()
    
    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        choice = input("Choose an option: ").strip()

        if choice == '1':
            auth.register_user()
        elif choice == '2':
            auth.login_user()
        elif choice == '3':
            break
        else:
            print("Invalid option")

if __name__ == "__main__":
    main()