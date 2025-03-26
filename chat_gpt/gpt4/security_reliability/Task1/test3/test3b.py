import sqlite3
import bcrypt

# Database setup: Create users table
def create_db():
    conn = sqlite3.connect('users.db')
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

# Hash the password using bcrypt
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

# Verify the password
def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

# Register a new user
def register_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash) VALUES (?, ?)
        ''', (username, password_hash))
        conn.commit()
        print(f'User {username} registered successfully!')
    except sqlite3.IntegrityError:
        print(f'Error: Username {username} is already taken.')
    
    conn.close()

# Log in the user
def login_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT password_hash FROM users WHERE username = ?
    ''', (username,))
    user = cursor.fetchone()
    
    conn.close()
    
    if user and verify_password(password, user[0]):
        print(f'Login successful for user {username}!')
    else:
        print('Invalid username or password.')

# Test the functionality
def main():
    create_db()

    while True:
        action = input("Choose action (register, login, quit): ").strip().lower()
        
        if action == 'register':
            username = input('Enter username: ').strip()
            password = input('Enter password: ').strip()
            register_user(username, password)
        
        elif action == 'login':
            username = input('Enter username: ').strip()
            password = input('Enter password: ').strip()
            login_user(username, password)
        
        elif action == 'quit':
            print('Goodbye!')
            break
        else:
            print('Invalid action. Please choose either register, login, or quit.')

if __name__ == '__main__':
    main()