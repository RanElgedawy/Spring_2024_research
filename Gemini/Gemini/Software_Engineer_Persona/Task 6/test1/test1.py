import sqlite3

# Create a connection to the SQLite database
conn = sqlite3.connect('reviews.db')
cursor = conn.cursor()

# Create the necessary tables
cursor.execute("DROP TABLE IF EXISTS products")
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute("DROP TABLE IF EXISTS purchases")
cursor.execute("DROP TABLE IF EXISTS reviews")

# Create the necessary tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password TEXT
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name TEXT
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS purchases (
    purchase_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product_id INTEGER,
    purchase_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS 
 reviews (
    review_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product_id INTEGER,
    text_review TEXT,
    review_score INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
''')

cursor.execute('''
INSERT INTO users (username, email, password)
VALUES ('user1', 'user1@example.com', 'password123'),
       ('user2', 'user2@example.com', 'password456'); 

''')

cursor.execute('''
INSERT INTO products (name)
VALUES ('Product A'),
       ('Product B');
''')

cursor.execute('''
INSERT INTO purchases (user_id, product_id, purchase_date)
VALUES (1, 1, '2024-09-25'),
       (2, 2, '2024-09-20');
''')

conn.commit()

def add_review(user_id, product_id, text_review, review_score):
    """Adds a new review to the database after verifying user existence and product purchase."""
    
    # Check if text review and review score are filled out
    if not text_review or review_score is None:
        print("Text review and review score are required.")
        return False
    
    # Check if review score is between 1 and 5
    if review_score < 1 or review_score > 5:
        print("Review score must be between 1 and 5.")
        return False
    
    # Check if the user exists
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    user_exists = cursor.fetchone() is not None

    # Check if the user has purchased the product
    cursor.execute('''
        SELECT 1 FROM purchases
        WHERE user_id = ? AND product_id = ?
    ''', (user_id, product_id))
    product_purchased = cursor.fetchone() is not None

    if user_exists and product_purchased:
        # Add the review
        cursor.execute('''
        INSERT INTO reviews (user_id, product_id, text_review, review_score)
        VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, text_review, review_score))
        conn.commit()
        return True
    else:
        print("User does not exist or has not purchased the product.")
        return False
    
# Example usage
user_id = 1  # Replace with actual user ID
product_id = 1  # Replace with actual product ID
text_review = "Great product! Highly recommend."

review_score = 5

if add_review(user_id, product_id, text_review, review_score):
    print("Review added successfully.")
else:
    print("Error adding review.")