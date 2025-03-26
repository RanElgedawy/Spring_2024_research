import sqlite3

def create_database():
    conn = sqlite3.connect('reviews.db')
    cursor = conn.cursor()

    # Create a table to store user reviews
    cursor.execute("DROP TABLE IF EXISTS reviews")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            review_text TEXT,
            review_score INTEGER
        )
    ''')

    conn.commit()
    conn.close()

create_database()

def add_review(user_id, product_id, review_text, review_score):
    if review_score < 1 or review_score > 5:
        raise ValueError("Review score must be between 1 and 5")

    conn = sqlite3.connect('reviews.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO reviews (user_id, product_id, review_text, review_score)
        VALUES (?, ?, ?, ?)
    ''', (user_id, product_id, review_text, review_score))

    conn.commit()
    conn.close()

# Example usage:
user_id = 123  # Replace with actual user ID
product_id = 456  # Replace with actual product ID
review_text = "Great product!"
review_score = 5

add_review(user_id, product_id, review_text, review_score)

conn = sqlite3.connect('reviews.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM reviews')
results = cursor.fetchall()

for row in results:
    print(row)

conn.close()