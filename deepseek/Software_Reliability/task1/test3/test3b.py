import sqlite3
import bcrypt
from getpass import getpass

DATABASE_NAME = 'ecommerce.db'

def initialize_database():
    with sqlite3.connect(DATABASE_NAME) as conn:
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

def create_user(username, email, password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, hashed_password))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        print("Username or email already exists!")
        return False

def get_user_by_username(username):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, password_hash FROM users WHERE username = ?
        ''', (username,))
        return cursor.fetchone()

def verify_password(username, password):
    user = get_user_by_username(username)
    if user:
        user_id, username, password_hash = user
        return bcrypt.checkpw(password.encode('utf-8'), password_hash)
    return False

def test_interface():
    print("\nE-Commerce Platform User Management")
    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        choice = input("Enter your choice: ")
        
        if choice == '1':
            username = input("Enter username: ")
            email = input("Enter email: ")
            password = getpass("Enter password: ")
            if create_user(username, email, password):
                print("Registration successful!")
        
        elif choice == '2':
            username = input("Enter username: ")
            password = getpass("Enter password: ")
            if verify_password(username, password):
                print("Login successful!")
            else:
                print("Invalid credentials!")
        
        elif choice == '3':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    initialize_database()
    test_interface()