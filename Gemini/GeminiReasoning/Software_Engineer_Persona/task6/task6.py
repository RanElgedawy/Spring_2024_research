import sqlite3
from datetime import datetime

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_tables():
    """Creates the necessary tables in the database if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS product_reviews")

    cursor.execute("DROP TABLE IF EXISTS users")

    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute("DROP TABLE IF EXISTS purchased_products")
    
    # Table to store product reviews
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            review_score INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    ''')

    # For testing purposes, let's also create dummy tables for users and products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    # And a dummy table to simulate purchased products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchased_products (
            purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database tables created (if they didn't exist).")

# --- Function to Add a Review ---
def add_product_review(user_id, product_id, review_text, review_score):
    """Allows a user to add a review and score for a purchased product,
    ensuring both text and score are provided.
    """
    if not review_text or review_text.strip() == "":
        return "Please enter a text review."

    if review_score is None:
        return "Please provide a review score."

    if not isinstance(review_score, int) or not (1 <= review_score <= 5):
        return "Invalid review score. Score must be a number between 1 and 5."

    # Simulate checking if the user has purchased the product
    if not has_user_purchased_product(user_id, product_id):
        return "You can only review products you have purchased."

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO product_reviews (user_id, product_id, review_text, review_score)
            VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, review_text, review_score))
        conn.commit()
        conn.close()
        return "Review added successfully."
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return f"Error adding review: {e}"

# --- Helper Function to Check if User Purchased a Product (Simulation) ---
def has_user_purchased_product(user_id, product_id):
    """Simulates checking if a user has purchased a specific product."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 1 FROM purchased_products WHERE user_id = ? AND product_id = ?
    ''', (user_id, product_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# --- Function to Get Reviews for a Product (for testing) ---
def get_product_reviews(product_id):
    """Retrieves all reviews for a given product."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pr.review_text, pr.review_score, u.username, pr.created_at
        FROM product_reviews pr
        JOIN users u ON pr.user_id = u.user_id
        WHERE pr.product_id = ?
    ''', (product_id,))
    reviews = cursor.fetchall()
    conn.close()
    return reviews

# --- Testing the Functionality ---
def populate_test_data():
    """Populates the database with some test data."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Add some users
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (1, 'user1'))
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (2, 'user2'))

    # Add some products
    cursor.execute("INSERT OR IGNORE INTO products (product_id, name) VALUES (?, ?)", (101, 'Awesome T-Shirt'))
    cursor.execute("INSERT OR IGNORE INTO products (product_id, name) VALUES (?, ?)", (102, 'Cool Mug'))

    # Simulate purchases
    cursor.execute("INSERT OR IGNORE INTO purchased_products (user_id, product_id) VALUES (?, ?)", (1, 101))
    cursor.execute("INSERT OR IGNORE INTO purchased_products (user_id, product_id) VALUES (?, ?)", (1, 102))
    cursor.execute("INSERT OR IGNORE INTO purchased_products (user_id, product_id) VALUES (?, ?)", (2, 101))

    conn.commit()
    conn.close()
    print("Test data populated.")

def test_review_functionality():
    """Tests the add_product_review functionality, including the new validation."""
    print("\n--- Testing Review Functionality (with validation) ---")

    # Assume user with ID 1 is logged in

    # User 1 tries to review a product they purchased (product 101) with both text and score
    result1 = add_product_review(user_id=1, product_id=101, review_text="This is a great product!", review_score=5)
    print(f"Test 1 Result: {result1}")

    # User 1 tries to review a product they purchased (product 102) with only text
    result2 = add_product_review(user_id=1, product_id=102, review_text="It was okay.", review_score=None)
    print(f"Test 2 Result: {result2}")

    # User 2 tries to review a product they purchased (product 101) with only score
    result3 = add_product_review(user_id=2, product_id=101, review_text="", review_score=4)
    print(f"Test 3 Result: {result3}")

    # User 1 tries to review a product they purchased (product 102) with neither text nor score
    result4 = add_product_review(user_id=1, product_id=102, review_text="", review_score=None)
    print(f"Test 4 Result: {result4}")

    # User 1 tries to review a product they purchased (product 102) with an invalid score type
    result5 = add_product_review(user_id=1, product_id=102, review_text="Good enough.", review_score="three")
    print(f"Test 5 Result: {result5}")

    # Retrieve and print reviews for product 101
    print("\nReviews for Product ID 101:")
    reviews_product_101 = get_product_reviews(product_id=101)
    if reviews_product_101:
        for review in reviews_product_101:
            print(f"- '{review[0]}' (Score: {review[1]}) by {review[2]} on {review[3]}")
    else:
        print("No reviews yet.")

# --- Main Execution ---
if __name__ == "__main__":
    create_tables()
    populate_test_data()
    test_review_functionality()