from flask import Flask, request, redirect, url_for, render_template_string, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

DATABASE = 'reviews.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database and create tables if they don't exist."""
    # If the DB file does not exist, create it along with the tables.
    # if not os.path.exists(DATABASE):
    conn = get_db_connection()
    with conn:
        conn.execute("DROP TABLE IF EXISTS reviews")
        conn.execute("DROP TABLE IF EXISTS purchases")
        # Table for storing reviews
        conn.execute('''
            CREATE TABLE reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                review_text TEXT,
                review_score INTEGER CHECK(review_score BETWEEN 1 AND 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        # Table for simulating purchased products.
        conn.execute('''
            CREATE TABLE purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        # Insert some test purchase records.
        # Here we assume user 1 purchased products with IDs 101 and 102.
        conn.execute("INSERT INTO purchases (user_id, product_id) VALUES (1, 101);")
        conn.execute("INSERT INTO purchases (user_id, product_id) VALUES (1, 102);")
        # Optionally, add a purchase for another user to demonstrate access control.
        conn.execute("INSERT INTO purchases (user_id, product_id) VALUES (2, 103);")
    conn.close()

# Initialize the database on startup.
init_db()

# Simulate a logged-in user.
@app.before_request
def simulate_login():
    # In a real application, this would be set after authenticating the user.
    session['user_id'] = 1

@app.route('/')
def index():
    """Home page: display purchased products and a form to submit reviews."""
    user_id = session.get('user_id')
    conn = get_db_connection()
    # Retrieve all products purchased by the current user.
    purchases = conn.execute("SELECT * FROM purchases WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    
    # Render a simple HTML page with a review form for each purchased product.
    html = """
    <h1>Submit a Review</h1>
    {% for purchase in purchases %}
        <h2>Product ID: {{ purchase['product_id'] }}</h2>
        <form method="post" action="{{ url_for('submit_review') }}">
            <input type="hidden" name="product_id" value="{{ purchase['product_id'] }}">
            <textarea name="review_text" placeholder="Enter your review" rows="3" cols="40" required></textarea><br>
            <label for="review_score">Rating (1-5):</label>
            <input type="number" name="review_score" min="1" max="5" required><br>
            <input type="submit" value="Submit Review">
        </form>
        <hr>
    {% endfor %}
    <a href="{{ url_for('view_reviews') }}">View My Reviews</a>
    """
    return render_template_string(html, purchases=purchases)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    """Endpoint to handle review submissions."""
    user_id = session.get('user_id')
    product_id = request.form.get('product_id')
    review_text = request.form.get('review_text')
    review_score = request.form.get('review_score')
    
    # Validate the review score to be an integer between 1 and 5.
    try:
        review_score = int(review_score)
        if review_score < 1 or review_score > 5:
            return "Review score must be between 1 and 5", 400
    except (ValueError, TypeError):
        return "Invalid review score", 400
    
    conn = get_db_connection()
    # Ensure the user has purchased this product.
    purchase = conn.execute("SELECT * FROM purchases WHERE user_id = ? AND product_id = ?",
                            (user_id, product_id)).fetchone()
    if not purchase:
        conn.close()
        return "You have not purchased this product", 403
    
    # Insert the review into the database.
    with conn:
        conn.execute(
            "INSERT INTO reviews (user_id, product_id, review_text, review_score) VALUES (?, ?, ?, ?)",
            (user_id, product_id, review_text, review_score)
        )
    conn.close()
    return redirect(url_for('index'))

@app.route('/view_reviews')
def view_reviews():
    """Display all reviews submitted by the current user."""
    user_id = session.get('user_id')
    conn = get_db_connection()
    reviews = conn.execute("SELECT * FROM reviews WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    
    html = """
    <h1>My Reviews</h1>
    {% if reviews %}
        {% for review in reviews %}
            <h2>Product ID: {{ review['product_id'] }} - Rating: {{ review['review_score'] }}</h2>
            <p>{{ review['review_text'] }}</p>
            <small>Submitted on: {{ review['created_at'] }}</small>
            <hr>
        {% endfor %}
    {% else %}
        <p>No reviews submitted yet.</p>
    {% endif %}
    <a href="{{ url_for('index') }}">Back</a>
    """
    return render_template_string(html, reviews=reviews)

if __name__ == '__main__':
    app.run(debug=True)
