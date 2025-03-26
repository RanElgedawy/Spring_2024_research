import sqlite3
import hashlib

conn = sqlite3.connect('ecommerce.db')
c = conn.cursor()

# Create a table to store user information
c.execute("DROP TABLE IF EXISTS users")
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    email TEXT
)''')

conn.commit()
conn.close()

def register_user(username, password, email):
    if not all([username, password, email]):
        return "Missing required fields (username, password, email)"
    
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    # Hash the password for security
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Check if the username already exists
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    if result:
        return "Username already exists"

    # Insert the user into the database
    c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, hashed_password, email))
    conn.commit()
    conn.close()

    return "Registration successful"

def login_user(username, password):
    if not all([username, password]):
        return "Missing required fields (username, password)"
    
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    # Hash the password and check if it matches
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password)) 

    result = c.fetchone()
    if result:
        return "Login successful"
    else:
        return "Invalid username or password"
    
# Example usage
if __name__ == "__main__":
    register_user("john_doe", "password123", "john_doe@example.com")
    login_status = login_user("john_doe", "password123")
    print(login_status)