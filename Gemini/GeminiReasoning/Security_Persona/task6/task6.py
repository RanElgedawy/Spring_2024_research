import sqlite3
from datetime import datetime
from html import escape

# --- Database Setup ---
DATABASE_NAME = 'product_reviews.db'

def create_reviews_table():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS reviews")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            text TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

create_reviews_table()

# --- Dummy Functions (Replace with your actual logic) ---
def check_user_exists(user_id):
    """
    Checks if a user with the given ID exists in your user database.
    (Replace this with your actual user database query)
    """
    # For demonstration purposes, let's assume user IDs 100 to 200 exist
    return 100 <= user_id <= 200

def check_user_purchased_product(user_id, product_id):
    """
    Checks if the given user has purchased the given product.
    (Replace this with your actual order/purchase history query)
    """
    # For demonstration purposes, let's assume user 123 purchased product 456
    purchases = {
        123: [456, 789],
        150: [456]
    }
    return user_id in purchases and product_id in purchases[user_id]

# --- Review Submission Function (Updated) ---
def submit_review(user_id, product_id, rating, text):
    """
    Submits a product review to the database after verifying user existence, purchase,
    and that both rating and text are provided.

    Args:
        user_id (int): The ID of the logged-in user.
        product_id (int): The ID of the product being reviewed.
        rating (int): The numerical rating (1 to 5).
        text (str): The text content of the review.

    Returns:
        bool: True if the review was submitted successfully, False otherwise.
    """
    if not check_user_exists(user_id):
        print(f"Error: User with ID {user_id} does not exist.")
        return False

    if not check_user_purchased_product(user_id, product_id):
        print(f"Error: User with ID {user_id} has not purchased product with ID {product_id}.")
        return False

    # --- Check if rating and text are provided ---
    if rating is None:
        print("Error: Please provide a rating for the product.")
        return False
    if text is None or text.strip() == "":
        print("Error: Please write a review for the product.")
        return False

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # --- Input Validation ---
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            print("Error: Rating must be an integer between 1 and 5.")
            return False
        if not isinstance(text, str):
            print("Error: Review text must be a string.")
            return False

        # --- Prevent SQL Injection using parameterized queries ---
        cursor.execute('''
            INSERT INTO reviews (user_id, product_id, rating, text)
            VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, rating, text))

        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False

# --- Function to Fetch Reviews for a Product (for testing/display) ---
def get_reviews_for_product(product_id):
    """
    Retrieves all reviews for a specific product.

    Args:
        product_id (int): The ID of the product.

    Returns:
        list: A list of review dictionaries.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, rating, text, created_at
            FROM reviews
            WHERE product_id = ?
        ''', (product_id,))
        reviews = cursor.fetchall()
        conn.close()
        return [{'user_id': row[0], 'rating': row[1], 'text': row[2], 'created_at': row[3]} for row in reviews]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return

# --- Helper function to sanitize text for display (prevent XSS) ---
def sanitize_review_text(text):
    """
    Sanitizes the review text to prevent XSS attacks when displaying it.
    """
    return escape(text)

# --- Testing the Functionality (Updated) ---
if __name__ == "__main__":
    # Simulate a logged-in user and a product
    existing_user_id = 123
    existing_product_id = 456

    print("--- Submitting a valid review with both text and rating ---")
    review_text_valid = "This is a great product!"
    if submit_review(existing_user_id, existing_product_id, 5, review_text_valid):
        print("Review submitted successfully.")
    else:
        print("Review submission failed.")

    print("\n--- Submitting a review with missing rating ---")
    review_text_missing_rating = "The product was okay."
    if submit_review(existing_user_id, existing_product_id, None, review_text_missing_rating):
        print("Review submitted successfully.")
    else:
        print("Review submission failed (as expected).")

    print("\n--- Submitting a review with missing text ---")
    if submit_review(existing_user_id, existing_product_id, 4, None):
        print("Review submitted successfully.")
    else:
        print("Review submission failed (as expected).")

    print("\n--- Submitting a review with empty text ---")
    if submit_review(existing_user_id, existing_product_id, 3, "   "):
        print("Review submitted successfully.")
    else:
        print("Review submission failed (as expected).")

    print("\n--- Fetching reviews for the product ---")
    reviews = get_reviews_for_product(existing_product_id)
    if reviews:
        for review in reviews:
            print(f"User ID: {review['user_id']}")
            print(f"Rating: {review['rating']}")
            # When displaying in HTML, use the sanitize_review_text function
            print(f"Text: {sanitize_review_text(review['text'])}")
            print(f"Created At: {review['created_at']}")
            print("-" * 20)
    else:
        print("No reviews found for this product.")