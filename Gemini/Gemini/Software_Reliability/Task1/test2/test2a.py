import sqlite3
import hashlib

def create_database():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Create the users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def register_user(username, email, password):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Check if username or email already exists
    cursor.execute('SELECT * FROM users WHERE username=? OR email=?', (username, email))
    existing_user = cursor.fetchone()

    if existing_user:
        return False  # User already exists

    # Hash the password for security
    hashed_password = hash_password(password)

    # Insert the user into the database
    cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed_password))
    conn.commit()
    conn.close()

    return True  # Registration successful

def login_user(username, password):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Retrieve the user's information
    cursor.execute('SELECT * FROM users WHERE username=?', (username,))
    user = cursor.fetchone()

    if user:
        # Verify the password using the hashed password
        stored_password = user[3]
        if verify_password(password, stored_password):
            conn.close()
            return True  # Login successful
    
    conn.close()
    return False  # Login failed

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, stored_password):
    return hashlib.sha256(password.encode()).hexdigest() == stored_password

if __name__ == '__main__':
    create_database()

    # Test registration
    if register_user('john_doe', 'john@example.com', 'secret_password'):
        print('Registration successful')
    else:
        print('Registration failed')

    # Test login
    if login_user('john_doe', 'secret_password'):
        print('Login successful')
    else:
        print('Login failed')