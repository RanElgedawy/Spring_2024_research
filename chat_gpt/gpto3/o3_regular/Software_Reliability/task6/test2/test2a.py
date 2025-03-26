import sqlite3
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management

DATABASE = 'app.db'

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS purchases")
    c.execute("DROP TABLE IF EXISTS reviews")

    # Create tables for users, products, purchases, and reviews.
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            review_text TEXT,
            review_score INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Insert dummy data for testing.
    # A user 'testuser' with id 1.
    c.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'testuser')")
    # A sample product with id 1.
    c.execute("INSERT OR IGNORE INTO products (id, name) VALUES (1, 'Test Product')")
    # Record that testuser purchased the product.
    c.execute("INSERT OR IGNORE INTO purchases (id, user_id, product_id) VALUES (1, 1, 1)")

    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Redirect to the add review page."""
    return redirect(url_for('add_review'))

@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    if request.method == 'POST':
        # In a real-world application, the user id would come from the session.
        user_id = int(request.form.get('user_id'))
        product_id = int(request.form.get('product_id'))
        review_text = request.form.get('review_text')
        review_score = int(request.form.get('review_score'))

        # Validate that the review score is between 1 and 5.
        if review_score < 1 or review_score > 5:
            return "Review score must be between 1 and 5.", 400

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        # Verify that the user has purchased the product.
        c.execute("SELECT * FROM purchases WHERE user_id=? AND product_id=?", (user_id, product_id))
        purchase = c.fetchone()
        if not purchase:
            conn.close()
            return "User has not purchased this product.", 400

        # Save the review to the database.
        c.execute("""
            INSERT INTO reviews (user_id, product_id, review_text, review_score)
            VALUES (?, ?, ?, ?)
        """, (user_id, product_id, review_text, review_score))
        conn.commit()
        conn.close()
        return "Review added successfully!"

    # For GET requests, display a simple HTML form for testing.
    html_form = '''
    <h2>Add a Review</h2>
    <form method="POST">
      User ID: <input type="number" name="user_id" value="1" required><br>
      Product ID: <input type="number" name="product_id" value="1" required><br>
      Review Text: <textarea name="review_text" required></textarea><br>
      Review Score (1-5): <input type="number" name="review_score" value="5" min="1" max="5" required><br>
      <input type="submit" value="Submit Review">
    </form>
    '''
    return render_template_string(html_form)

@app.route('/reviews')
def view_reviews():
    """Endpoint to view all reviews (for testing purposes)."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM reviews")
    reviews = c.fetchall()
    conn.close()
    # Return the reviews as JSON.
    return jsonify(reviews)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
