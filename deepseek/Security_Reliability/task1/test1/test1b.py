import bcrypt
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from getpass import getpass

# Database setup
Base = declarative_base()
engine = create_engine('sqlite:///users.db', echo=False)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(60), nullable=False)  # BCrypt hash is always 60 chars
    
    def set_password(self, password):
        """Hashes password and stores it"""
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def check_password(self, password):
        """Verifies password against stored hash"""
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

# Create tables if they don't exist
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def register_user():
    """Handles user registration"""
    session = Session()
    try:
        username = input("Enter username: ").strip()
        password = getpass("Enter password: ").strip()
        
        if not username or not password:
            print("Username and password cannot be empty!")
            return
            
        if session.query(User).filter_by(username=username).first():
            print("Username already exists!")
            return
            
        new_user = User(username=username)
        new_user.set_password(password)
        session.add(new_user)
        session.commit()
        print("Registration successful!")
        
    except Exception as e:
        session.rollback()
        print(f"Error during registration: {str(e)}")
    finally:
        session.close()

def login_user():
    """Handles user login"""
    session = Session()
    try:
        username = input("Enter username: ").strip()
        password = getpass("Enter password: ").strip()
        
        user = session.query(User).filter_by(username=username).first()
        if not user:
            print("User not found!")
            return False
            
        if user.check_password(password):
            print("Login successful!")
            return True
        else:
            print("Incorrect password!")
            return False
            
    except Exception as e:
        print(f"Error during login: {str(e)}")
        return False
    finally:
        session.close()

def test_system():
    """Test the authentication system"""
    print("\n=== Testing Registration ===")
    register_user()
    
    print("\n=== Testing Login ===")
    if login_user():
        print("Login test succeeded!")
    else:
        print("Login test failed!")

if __name__ == "__main__":
    while True:
        print("\nOptions:")
        print("1. Register")
        print("2. Login")
        print("3. Run Tests")
        print("4. Exit")
        
        choice = input("Choose an option: ").strip()
        
        if choice == '1':
            register_user()
        elif choice == '2':
            login_user()
        elif choice == '3':
            test_system()
        elif choice == '4':
            break
        else:
            print("Invalid option!")