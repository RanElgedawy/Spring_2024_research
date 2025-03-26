import sqlite3
import bcrypt

class AuthSystem:
    def __init__(self, db_name='users.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_table()
        
    def create_table(self):
        """Create users table if it doesn't exist"""
        self.conn.execute("DROP TABLE IF EXISTS users")
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def register_user(self, username, password):
        """Register a new user with hashed password"""
        if self.user_exists(username):
            return False, "Username already exists"
        
        # Hash password with bcrypt (auto-generated salt)
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        try:
            self.conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, hashed)
            )
            self.conn.commit()
            return True, "Registration successful"
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"

    def login_user(self, username, password):
        """Authenticate user with password"""
        cursor = self.conn.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        
        if not result:
            return False, "User not found"
        
        stored_hash = result[0]
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return True, "Login successful"
        return False, "Invalid password"

    def user_exists(self, username):
        """Check if username exists in database"""
        cursor = self.conn.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (username,)
        )
        return cursor.fetchone() is not None

    def close(self):
        """Close database connection"""
        self.conn.close()

def test_system():
    """Test the authentication system"""
    auth = AuthSystem()
    
    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        choice = input("Choose option: ").strip()
        
        if choice == '3':
            break
            
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        if choice == '1':
            success, message = auth.register_user(username, password)
            print(f"{'Success:' if success else 'Error:'} {message}")
            
        elif choice == '2':
            success, message = auth.login_user(username, password)
            print(f"{'Success:' if success else 'Error:'} {message}")
    
    auth.close()

if __name__ == "__main__":
    test_system()