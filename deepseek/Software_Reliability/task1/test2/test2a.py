import sqlite3
import bcrypt
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db_name='ecommerce.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def register_user(self, username, password, email):
        if self.is_username_taken(username):
            return False, "Username already taken"
        if self.is_email_taken(email):
            return False, "Email already registered"

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password_hash, email)
                VALUES (?, ?, ?)
            ''', (username, hashed_password.decode('utf-8'), email))
            self.conn.commit()
            return True, "Registration successful"
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"

    def verify_user(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT password_hash FROM users WHERE username = ?
        ''', (username,))
        result = cursor.fetchone()
        
        if not result:
            return False, "User not found"
        
        stored_hash = result[0].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return True, "Login successful"
        return False, "Invalid password"

    def is_username_taken(self, username):
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
        return cursor.fetchone() is not None

    def is_email_taken(self, email):
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE email = ?', (email,))
        return cursor.fetchone() is not None

    def close(self):
        self.conn.close()

def test_auth_flow():
    db = DatabaseHandler()
    
    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            email = input("Enter email: ")
            
            success, message = db.register_user(username, password, email)
            print(f"{'Success!' if success else 'Error'}: {message}")

        elif choice == '2':
            username = input("Enter username: ")
            password = input("Enter password: ")
            
            success, message = db.verify_user(username, password)
            print(f"{'Success!' if success else 'Error'}: {message}")

        elif choice == '3':
            db.close()
            print("Goodbye!")
            break

        else:
            print("Invalid option, try again")

if __name__ == "__main__":
    test_auth_flow()