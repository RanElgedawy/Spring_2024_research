import bcrypt
import sqlite3

def create_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL
                 )''')

    conn.commit()
    conn.close()

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def register_user(username, password):
    if not username or not password:
        raise ValueError("Username and password are required.")
    
    hashed_password = hash_password(password)
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Username already exists
        return False
    finally:
        conn.close()

def login_user(username, password):
    if not username or not password:
        raise ValueError("Username and password are required.")
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    try:
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = c.fetchone()

        if result:
            hashed_password = result[0]
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                return True
            else:
                return False
        else:
            return False
    finally:
        conn.close()

# Test the functionality
create_database()
print(register_user("john_doe", "password123")) # Output: False if already registered
print(login_user("john_doe", "password123"))  # Output: True
print(login_user("john_doe", "wrong_password"))  # Output: False

# Test missing parameters
try:
    register_user("john_doe", "")
except ValueError as e:
    print(e)  # Output: Username and password are required.