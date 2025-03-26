import sqlite3
from contextlib import closing

# Database connection setup
DATABASE_NAME = 'ecommerce.db'

def initialize_database():
    with closing(sqlite3.connect(DATABASE_NAME)) as conn:
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS purchases")
        cursor.execute("DROP TABLE IF EXISTS reviews")

        # Create necessary tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                user_id INTEGER,
                product_id INTEGER,
                purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                review_text TEXT,
                review_score INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(product_id) REFERENCES products(id),
                UNIQUE(user_id, product_id),
                CHECK (review_score BETWEEN 1 AND 5)
            )
        ''')
        
        # Insert test data
        cursor.executemany(
            'INSERT OR IGNORE INTO users (username, email) VALUES (?, ?)',
            [('test_user', 'user@example.com'), ('another_user', 'another@example.com')]
        )
        
        cursor.executemany(
            'INSERT OR IGNORE INTO products (name, price) VALUES (?, ?)',
            [('Test Product', 99.99), ('Another Product', 199.99)]
        )
        
        cursor.executemany(
            'INSERT OR IGNORE INTO purchases (user_id, product_id) VALUES (?, ?)',
            [(1, 1), (1, 2)]
        )
        
        conn.commit()

def add_product_review(user_id, product_id, review_text, review_score):
    with closing(sqlite3.connect(DATABASE_NAME)) as conn:
        cursor = conn.cursor()
        
        try:
            # Verify purchase exists
            cursor.execute('''
                SELECT 1 FROM purchases 
                WHERE user_id = ? AND product_id = ?
            ''', (user_id, product_id))
            
            if not cursor.fetchone():
                raise ValueError("User hasn't purchased this product")
            
            # Insert review
            cursor.execute('''
                INSERT INTO reviews 
                (user_id, product_id, review_text, review_score)
                VALUES (?, ?, ?, ?)
            ''', (user_id, product_id, review_text, review_score))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if 'UNIQUE' in str(e):
                raise ValueError("User already reviewed this product")
            elif 'CHECK' in str(e):
                raise ValueError("Review score must be between 1 and 5")
            else:
                raise ValueError("Database error occurred")

def test_review_system():
    initialize_database()
    
    # Test valid review
    try:
        add_product_review(1, 1, "Great product!", 5)
        print("Test 1 Passed: Valid review added")
    except Exception as e:
        print(f"Test 1 Failed: {str(e)}")
    
    # Test duplicate review
    try:
        add_product_review(1, 1, "Trying again", 4)
        print("Test 2 Failed: Duplicate review allowed")
    except ValueError as e:
        if "already reviewed" in str(e):
            print("Test 2 Passed: Duplicate review prevented")
        else:
            print(f"Test 2 Failed: {str(e)}")
    
    # Test invalid score
    try:
        add_product_review(1, 2, "Terrible!", 0)
        print("Test 3 Failed: Invalid score accepted")
    except ValueError as e:
        if "between 1 and 5" in str(e):
            print("Test 3 Passed: Invalid score rejected")
        else:
            print(f"Test 3 Failed: {str(e)}")
    
    # Test unauthorized review
    try:
        add_product_review(2, 1, "Not purchased", 3)
        print("Test 4 Failed: Unauthorized review accepted")
    except ValueError as e:
        if "hasn't purchased" in str(e):
            print("Test 4 Passed: Unauthorized review rejected")
        else:
            print(f"Test 4 Failed: {str(e)}")

if __name__ == "__main__":
    test_review_system()