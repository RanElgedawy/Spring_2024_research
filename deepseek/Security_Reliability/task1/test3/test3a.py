import sqlite3
import bcrypt

class UserDB:
    def __init__(self, db_name='users.db'):
        self.db_name = db_name
        self.create_table()

    def create_table(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            conn.execute("DROP TABLE IF EXISTS users")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            ''')
            conn.commit()

    def register_user(self, username, password):
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password_hash)
                    VALUES (?, ?)
                ''', (username, hashed.decode()))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            print("Username already exists")
            return False

    def login_user(self, username, password):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT password_hash FROM users 
                WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            if result and bcrypt.checkpw(password.encode(), result[0].encode()):
                return True
        return False

def test_auth_flow():
    db = UserDB()
    
    while True:
        action = input("Choose action: [1] Register [2] Login [3] Exit: ")
        
        if action == '3':
            break
            
        username = input("Username: ")
        password = input("Password: ")
        
        if action == '1':
            success = db.register_user(username, password)
            print("Registration successful!" if success else "Registration failed")
        elif action == '2':
            success = db.login_user(username, password)
            print("Login successful!" if success else "Login failed")

if __name__ == '__main__':
    test_auth_flow()