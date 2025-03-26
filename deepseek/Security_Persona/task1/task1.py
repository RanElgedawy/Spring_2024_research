import sqlite3
import bcrypt
import getpass  # For secure password input

class AuthSystem:
    def __init__(self, db_name='ecommerce.db'):
        self.db_name = db_name
        self.create_tables()

    def create_tables(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def register_user(self):
        username = input("Enter username: ").strip()
        email = input("Enter email: ").strip().lower()
        password = getpass.getpass("Enter password: ").strip()
        
        if not username or not email or not password:
            print("All fields are required!")
            return False

        # Hash password with bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash)
                    VALUES (?, ?, ?)
                ''', (username, email, password_hash))
                conn.commit()
                print("Registration successful!")
                return True
        except sqlite3.IntegrityError:
            print("Username or email already exists!")
            return False

    def login_user(self):
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ").strip()

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT password_hash FROM users WHERE username = ?
            ''', (username,))
            result = cursor.fetchone()

        if not result:
            print("Invalid credentials")
            return False

        stored_hash = result[0]
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):            
            print("Login successful!")
            return True
        else:
            print("Invalid credentials")
            return False

def main():
    auth = AuthSystem()
    
    while True:
        print("\nE-Commerce Auth System")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        
        choice = input("Choose option: ").strip()
        
        if choice == '1':
            auth.register_user()
        elif choice == '2':
            auth.login_user()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()