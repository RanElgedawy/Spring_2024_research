import sqlite3

# Create a connection to the database
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Create a table to store user information
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
)
''')

conn.commit()
conn.close()

def register_user(username, password, email):
    if not all([username, password, email]):
        raise ValueError("All fields are required.")
    
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, password, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Handle duplicate username or email
        return False
    finally:
        conn.close()

def login_user(username, password):
    if not all([username, password]):
        raise ValueError("Username and password are required.")
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result and password == result[2]:
            return True
        else:
            return False
    finally:
        conn.close()

def login_user(username, password):
    if not all([username, password]):
        raise ValueError("Username and password are required.")
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result and password == result[2]:
            return True
        else:
            return False
    finally:
        conn.close()

# Test registration
if register_user("john_doe", "password123", "john.doe@example.com"):
    print("Registration successful!")
else:
    print("Registration failed (duplicate username or email)")

if register_user("john_doe", "password123", "john.doe@example.com"):
    print("Registration successful!")
else:
    print("Registration failed (duplicate username or email)")
    
# Test login
if login_user("john_doe", "password123"):
    print("Login successful!")
else:
    print("Login failed")

try:
    register_user("john_doe", "", "john.doe@example.com")  # Missing password
except ValueError as e:
    print(e)  # Output: All fields are required.
try:
    login_user("", "password123")  # Missing username
except ValueError as e:
    print(e)  # Output: Username and password are required.