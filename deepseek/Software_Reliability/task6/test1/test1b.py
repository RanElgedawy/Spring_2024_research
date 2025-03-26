import sqlite3
from datetime import datetime

# Database setup
conn = sqlite3.connect('ecommerce.db')
conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints

def setup_database():
    # Create tables if they don't exist
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute("DROP TABLE IF EXISTS products")
    conn.execute("DROP TABLE IF EXISTS purchases")
    conn.execute("DROP TABLE IF EXISTS reviews")

    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL)''')

    conn.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    price REAL NOT NULL)''')

    conn.execute('''CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    purchase_date TIMESTAMP NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(product_id) REFERENCES products(id))''')

    conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    review_text TEXT,
                    review_score INTEGER NOT NULL CHECK (review_score BETWEEN 1 AND 5),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(product_id) REFERENCES products(id),
                    UNIQUE(user_id, product_id))''')
    conn.commit()

def add_review(user_id, product_id, review_text, review_score):
    # Validate review score
    if not 1 <= review_score <= 5:
        raise ValueError("Review score must be between 1 and 5")

    # Check if user has purchased the product
    cursor = conn.execute('''SELECT id FROM purchases 
                           WHERE user_id = ? AND product_id = ?''',
                           (user_id, product_id))
    if not cursor.fetchone():
        raise PermissionError("User hasn't purchased this product")

    # Insert review
    try:
        conn.execute('''INSERT INTO reviews 
                      (user_id, product_id, review_text, review_score)
                      VALUES (?, ?, ?, ?)''',
                      (user_id, product_id, review_text, review_score))
        conn.commit()
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise ValueError("User already reviewed this product") from e
        raise

# Test functions
def create_test_data():
    # Create test user
    conn.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'test_user')")
    # Create test product
    conn.execute("INSERT OR IGNORE INTO products (id, name, price) VALUES (1, 'Test Product', 99.99)")
    # Create test purchase
    conn.execute('''INSERT OR IGNORE INTO purchases 
                  (user_id, product_id, purchase_date)
                  VALUES (1, 1, ?)''', (datetime.now(),))
    conn.commit()

def test_review_functionality():
    print("=== Testing Review Functionality ===")
    
    # Test valid review
    try:
        add_review(1, 1, "", 5)
        print("Test 1 Passed: Valid review added")
    except Exception as e:
        print(f"Test 1 Failed: {str(e)}")

    # Test duplicate review
    try:
        add_review(1, 1, "Trying again", 3)
        print("Test 2 Failed: Duplicate review allowed")
    except ValueError as e:
        print(f"Test 2 Passed: {str(e)}")

    # Test invalid product
    try:
        add_review(1, 999, "Invalid product", 4)
        print("Test 3 Failed: Review for unpurchased product allowed")
    except PermissionError as e:
        print(f"Test 3 Passed: {str(e)}")

    # Test invalid score
    try:
        add_review(1, 1, "Invalid score", 6)
        print("Test 4 Failed: Invalid score accepted")
    except ValueError as e:
        print(f"Test 4 Passed: {str(e)}")

if __name__ == "__main__":
    setup_database()
    create_test_data()
    test_review_functionality()
    conn.close()