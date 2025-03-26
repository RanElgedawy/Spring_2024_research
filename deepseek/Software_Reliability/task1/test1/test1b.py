import sqlite3
import bcrypt
from getpass import getpass

DATABASE_NAME = 'ecommerce.db'

def initialize_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Create users table
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
    conn.close()

def register_user():
    print("\n--- Registration ---")
    username = input("Enter username: ").strip()
    email = input("Enter email: ").strip()
    password = getpass("Enter password: ").strip()
    
    if not username or not email or not password:
        print("All fields are required!")
        return

    # Hash password with bcrypt
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        
        conn.commit()
        print("Registration successful!")
    except sqlite3.IntegrityError:
        print("Username or email already exists!")
    finally:
        conn.close()

def login_user():
    print("\n--- Login ---")
    username = input("Username: ").strip()
    password = getpass("Password: ").strip()
    
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT password_hash FROM users WHERE username = ?
    ''', (username,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
        print("Login successful!")
    else:
        print("Invalid credentials!")

def main_menu():
    initialize_database()
    
    while True:
        print("\nE-Commerce Platform")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        
        choice = input("Enter your choice: ").strip()
        
        if choice == '1':
            register_user()
        elif choice == '2':
            login_user()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    # Install bcrypt if not already installed: pip install bcrypt
    main_menu()