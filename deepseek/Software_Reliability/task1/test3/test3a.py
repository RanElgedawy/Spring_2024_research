import sqlite3
import bcrypt
import datetime

# Database initialization
def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL,
                      email TEXT UNIQUE NOT NULL,
                      created_at DATETIME NOT NULL)''')
    conn.commit()

# User registration
def register_user(conn, username, password, email):
    try:
        cursor = conn.cursor()
        
        # Check for existing user
        cursor.execute('SELECT username, email FROM users WHERE username=? OR email=?', 
                      (username, email))
        if cursor.fetchone():
            return False

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user record
        created_at = datetime.datetime.now()
        cursor.execute('''INSERT INTO users 
                        (username, password, email, created_at)
                        VALUES (?, ?, ?, ?)''',
                        (username, hashed_password.decode('utf-8'), email, created_at))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# User login
def login_user(conn, username, password):
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE username=?', (username,))
    result = cursor.fetchone()
    
    if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
        return True
    return False

# Testing interface
def main():
    conn = sqlite3.connect('ecommerce.db')
    create_tables(conn)
    
    try:
        while True:
            print("\nE-Commerce Auth System")
            print("1. Register")
            print("2. Login")
            print("3. Exit")
            
            choice = input("Select option: ").strip()
            
            if choice == '1':
                username = input("Username: ").strip()
                password = input("Password: ").strip()
                email = input("Email: ").strip()
                
                if register_user(conn, username, password, email):
                    print("Registration successful!")
                else:
                    print("Registration failed (user already exists)")
                    
            elif choice == '2':
                username = input("Username: ").strip()
                password = input("Password: ").strip()
                
                if login_user(conn, username, password):
                    print("Login successful!")
                else:
                    print("Invalid credentials")
                    
            elif choice == '3':
                print("Goodbye!")
                break
                
            else:
                print("Invalid option")
    finally:
        conn.close()

if __name__ == "__main__":
    main()