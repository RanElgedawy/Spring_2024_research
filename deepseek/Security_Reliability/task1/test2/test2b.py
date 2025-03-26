import sqlite3
import bcrypt
import getpass  # For secure password input

class AuthSystem:
    def __init__(self, db_name='users.db'):
        self.db_name = db_name
        self._create_table()


    def _create_table(self):
        """Create users table if it doesn't exist"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            conn.execute("DROP TABLE IF EXISTS users")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def _get_db_connection(self):
        return sqlite3.connect(self.db_name)

    def register_user(self):
        """Register a new user with hashed password"""
        print("\n--- Registration ---")
        username = input("Enter username: ").strip()
        email = input("Enter email: ").strip()
        password = getpass.getpass("Enter password: ").strip()

        if not username or not password or not email:
            print("Error: All fields are required")
            return False

        # Hash password with bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email)
                    VALUES (?, ?, ?)
                ''', (username, hashed_password, email))
                conn.commit()
                print("Registration successful!")
                return True
        except sqlite3.IntegrityError as e:
            print(f"Error: {str(e)}")
            return False

    def login_user(self):
        """Authenticate user with password"""
        print("\n--- Login ---")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ").strip()

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT password_hash FROM users WHERE username = ?
            ''', (username,))
            result = cursor.fetchone()

        if not result:
            print("Invalid username or password")
            return False

        stored_hash = result[0]
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            print("Login successful!")
            return True
        else:
            print("Invalid username or password")
            return False

def test_auth_system():
    auth = AuthSystem()
    
    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        choice = input("Choose option: ").strip()

        if choice == '1':
            auth.register_user()
        elif choice == '2':
            auth.login_user()
        elif choice == '3':
            break
        else:
            print("Invalid option")

if __name__ == "__main__":
    test_auth_system()