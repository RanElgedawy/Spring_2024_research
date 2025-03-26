import sqlite3
import os
import hashlib

# Configuration
DB_NAME = 'users.db'
ITERATIONS = 100000   # Number of iterations for PBKDF2
HASH_ALGORITHM = 'sha256'
SALT_SIZE = 16        # 16 bytes of random salt

class UserAuth:
    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        """Creates the users table if it does not already exist."""
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def register_user(self, username, password):
        """Registers a new user by securely hashing the password."""
        cursor = self.conn.cursor()
        # Check if the username already exists
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone() is not None:
            print("Username already exists!")
            return False

        # Generate a secure random salt
        salt = os.urandom(SALT_SIZE)
        # Hash the password using PBKDF2_HMAC
        password_hash = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode('utf-8'),
            salt,
            ITERATIONS
        )
        # Store salt and hash as hexadecimal strings
        salt_hex = salt.hex()
        password_hash_hex = password_hash.hex()

        cursor.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                       (username, password_hash_hex, salt_hex))
        self.conn.commit()
        print("User registered successfully.")
        return True

    def verify_login(self, username, password):
        """Verifies user login by comparing the hash of the provided password to the stored hash."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash, salt FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row is None:
            print("Username does not exist!")
            return False

        stored_password_hash_hex, salt_hex = row
        salt = bytes.fromhex(salt_hex)
        # Recreate the hash with the provided password and stored salt
        password_hash = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode('utf-8'),
            salt,
            ITERATIONS
        )
        if password_hash.hex() == stored_password_hash_hex:
            print("Login successful!")
            return True
        else:
            print("Incorrect password!")
            return False

    def close(self):
        self.conn.close()

def main():
    auth = UserAuth()
    while True:
        print("\nSelect an option:")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Enter choice (1/2/3): ").strip()
        
        if choice == '1':
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            auth.register_user(username, password)
        elif choice == '2':
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            auth.verify_login(username, password)
        elif choice == '3':
            print("Exiting.")
            break
        else:
            print("Invalid choice, please try again.")

    auth.close()

if __name__ == '__main__':
    main()
