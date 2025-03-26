import sqlite3
import getpass

DATABASE = "newsletter.db"

def initialize_db():
    """Create the database tables if they do not exist and add sample users."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("DROP TABLE IF EXISTS users")
    # Create a table to store user details, including newsletter subscription status.
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            subscribed INTEGER DEFAULT 1,  -- 1 means subscribed, 0 means unsubscribed
            unsubscribe_reason TEXT
        )
    ''')
    
    # Insert sample users (for testing purposes)
    sample_users = [
        ("alice@example.com", "alicepass"),
        ("bob@example.com", "bobpass"),
    ]
    
    for email, password in sample_users:
        try:
            c.execute('''
                INSERT INTO users (email, password)
                VALUES (?, ?)
            ''', (email, password))
        except sqlite3.IntegrityError:
            # User already exists
            pass
    
    conn.commit()
    conn.close()

def verify_user(email, password):
    """Verify user identity by checking email and password."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        SELECT id, subscribed FROM users
        WHERE email = ? AND password = ?
    ''', (email, password))
    user = c.fetchone()
    conn.close()
    if user:
        return user  # returns tuple (id, subscribed)
    return None

def unsubscribe_user(user_id, reason=None):
    """Update the user's subscription status to unsubscribed and store the reason if provided."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        UPDATE users
        SET subscribed = 0,
            unsubscribe_reason = ?
        WHERE id = ?
    ''', (reason, user_id))
    conn.commit()
    conn.close()

def test_unsubscribe():
    print("=== Newsletter Unsubscription ===")
    email = input("Enter your email: ").strip()
    # For a simple demonstration, we use getpass to avoid echoing the password
    password = getpass.getpass("Enter your password: ").strip()
    
    user = verify_user(email, password)
    if not user:
        print("Error: Invalid credentials. Please try again.")
        return

    user_id, subscribed = user
    if subscribed == 0:
        print("You have already unsubscribed from the newsletter.")
        return
    
    confirm = input("Are you sure you want to unsubscribe from the newsletter? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Unsubscription cancelled.")
        return
    
    reason = input("Optional: Please provide a reason for unsubscribing (or press Enter to skip): ").strip()
    
    unsubscribe_user(user_id, reason if reason else None)
    print("You have successfully unsubscribed from the newsletter.")

def main():
    initialize_db()
    # For testing, we simply call the unsubscribe flow. In a real-world scenario, you might have a web framework route.
    test_unsubscribe()
    
    # Display updated user data (for testing purposes)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, email, subscribed, unsubscribe_reason FROM users")
    users = c.fetchall()
    print("\n--- Current Users Table ---")
    for u in users:
        print(u)
    conn.close()

if __name__ == "__main__":
    main()
