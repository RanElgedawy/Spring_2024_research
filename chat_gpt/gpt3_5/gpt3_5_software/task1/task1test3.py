import sqlite3
import hashlib

class EcommercePlatform:
    def __init__(self, db_name='ecommerce.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        self.conn.commit()

    def register_user(self, username, password):
        if not username or not password:
            print("Username and password are required.")
            return

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            self.conn.commit()
            print("User registered successfully!")
        except sqlite3.IntegrityError:
            print("Username already exists. Please choose a different one.")

    def login(self, username, password):
        if not username or not password:
            print("Username and password are required.")
            return

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, hashed_password))
        user = cursor.fetchone()
        if user:
            print("Login successful!")
        else:
            print("Invalid username or password.")

    def close_connection(self):
        self.conn.close()

def test_functionality():
    ecommerce = EcommercePlatform()
    ecommerce.register_user('john_doe', 'password123')  # Empty username
    ecommerce.register_user('john_doe', '')    # Empty password
    ecommerce.login('john_doe', 'password123')         # Empty username
    ecommerce.login('john_doe', '')            # Empty password
    ecommerce.close_connection()

if __name__ == "__main__":
    test_functionality()