import sqlite3
import bcrypt
from getpass import getpass
import datetime

class ECommerceDB:
    def __init__(self, db_name='ecommerce.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME NOT NULL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_username ON users (username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email ON users (email)')
        self.conn.commit()

    def register_user(self, username, email, password):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        created_at = datetime.datetime.now().isoformat()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
            ''', (username, email, hashed_password.decode('utf-8'), created_at))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print("Username or email already exists")
            return False

    def login_user(self, identifier, password):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, password_hash FROM users 
            WHERE username = ? OR email = ?
        ''', (identifier, identifier))
        
        user = cursor.fetchone()
        if user:
            user_id, stored_hash = user
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                return user_id
        return None

    def close(self):
        self.conn.close()

def test_registration_login():
    db = ECommerceDB()
    
    print("\n=== Registration Test ===")
    username = input("Enter username: ").strip()
    email = input("Enter email: ").strip()
    password = getpass("Enter password: ").strip()
    
    if db.register_user(username, email, password):
        print("\nRegistration successful!")
        
        print("\n=== Login Test ===")
        identifier = input("Enter username/email: ").strip()
        password = getpass("Enter password: ").strip()
        
        user_id = db.login_user(identifier, password)
        if user_id:
            print(f"\nLogin successful! User ID: {user_id}")
        else:
            print("\nLogin failed: Invalid credentials")

    db.close()

if __name__ == "__main__":
    test_registration_login()