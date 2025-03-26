from flask import Flask, request, g, render_template_string
import sqlite3

app = Flask(__name__)
DATABASE = 'reviews.db'

def get_db():
    """Get a database connection, creating one if necessary."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    """Initialize the database with required tables."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS reviews")
        cursor.execute("DROP TABLE IF EXISTS purchased_products")

        # Create a table for storing reviews.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                review_text TEXT,
                review_score INTEGER CHECK(review_score BETWEEN 1 AND 5)
            )
        """)
        # Optionally, create a dummy table for purchased products (for testing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchased_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_name TEXT
            )
        """)
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection when the app context ends."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    """Route for adding a review for a purchased product."""
    message = ''
    if request.method == 'POST':
        # For testing purposes, assume the logged-in user has ID 1.
        user_id = 1
        product_id = request.form.get('product_id')
        review_text = request.form.get('review_text')
        review_score = request.form.get('review_score')
        
        # Validate that product_id is provided
        if not product_id:
            message = "Please enter a valid product ID."
        else:
            # Validate review_score is an integer between 1 and 5.
            try:
                review_score = int(review_score)
                if review_score < 1 or review_score > 5:
                    raise ValueError
            except (ValueError, TypeError):
                message = "Review score must be an integer between 1 and 5."
            
        # If all validations pass, insert the review into the database.
        if not message:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO reviews (user_id, product_id, review_text, review_score) VALUES (?, ?, ?, ?)",
                (user_id, product_id, review_text, review_score)
            )
            db.commit()
            message = "Review added successfully!"
    
    # Simple HTML form for testing.
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Add Product Review</title>
      </head>
      <body>
        <h1>Add Review</h1>
        <p>{{ message }}</p>
        <form method="post">
          <label>Product ID:</label>
          <input type="text" name="product_id" required /><br/><br/>
          <label>Review Text:</label><br/>
          <textarea name="review_text" rows="4" cols="50" required></textarea><br/><br/>
          <label>Review Score (1-5):</label>
          <input type="number" name="review_score" min="1" max="5" required /><br/><br/>
          <input type="submit" value="Submit Review" />
        </form>
      </body>
    </html>
    """
    return render_template_string(html, message=message)

if __name__ == '__main__':
    init_db()  # Automatically create tables when starting the app.
    app.run(debug=True)
