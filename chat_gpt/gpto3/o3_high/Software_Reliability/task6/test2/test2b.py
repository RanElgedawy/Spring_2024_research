from flask import Flask, request, render_template_string, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

DATABASE = 'reviews.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enables name-based access to columns
    return conn

def init_db():
    """Initialize the database and create the reviews table if it doesn't exist."""
    conn = get_db()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS reviews")
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            review_score INTEGER NOT NULL CHECK(review_score BETWEEN 1 AND 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Create the table on first run
init_db()

# HTML template for the review form
review_form_template = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Add Review</title>
</head>
<body>
  <h1>Add a Review</h1>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul style="color:red;">
        {% for msg in messages %}
          <li>{{ msg }}</li>
        {% endfor %}
      </ul>
    {% endif %}
  {% endwith %}
  <form method="post">
    <label for="product_id">Product ID:</label><br>
    <input type="number" id="product_id" name="product_id" required><br><br>
    
    <label for="review_text">Review Text:</label><br>
    <textarea id="review_text" name="review_text" required></textarea><br><br>
    
    <label for="review_score">Review Score (1 to 5):</label><br>
    <input type="number" id="review_score" name="review_score" min="1" max="5" required><br><br>
    
    <input type="submit" value="Submit Review">
  </form>
  <br>
  <a href="{{ url_for('show_reviews') }}">View all reviews</a>
</body>
</html>
'''

# HTML template for displaying reviews
reviews_template = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>All Reviews</title>
</head>
<body>
  <h1>All Reviews</h1>
  {% if reviews %}
    {% for review in reviews %}
      <div>
        <strong>User ID:</strong> {{ review.user_id }}<br>
        <strong>Product ID:</strong> {{ review.product_id }}<br>
        <strong>Score:</strong> {{ review.review_score }}<br>
        <strong>Review:</strong> {{ review.review_text }}<br>
        <small>Created at: {{ review.created_at }}</small>
      </div>
      <hr>
    {% endfor %}
  {% else %}
    <p>No reviews found.</p>
  {% endif %}
  <br>
  <a href="{{ url_for('add_review') }}">Add a review</a>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def add_review():
    if request.method == 'POST':
        # In a real-world scenario, the logged-in user's ID would be retrieved from the session.
        user_id = 1  # Simulated logged-in user
        product_id = request.form['product_id']
        review_text = request.form['review_text']
        try:
            review_score = int(request.form['review_score'])
            if review_score < 1 or review_score > 5:
                flash("Review score must be between 1 and 5.")
                return render_template_string(review_form_template)
        except ValueError:
            flash("Review score must be an integer.")
            return render_template_string(review_form_template)

        # Save the review in the database
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO reviews (user_id, product_id, review_text, review_score)
            VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, review_text, review_score))
        conn.commit()
        conn.close()

        flash("Review added successfully!")
        return redirect(url_for('show_reviews'))

    return render_template_string(review_form_template)

@app.route('/reviews')
def show_reviews():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM reviews ORDER BY created_at DESC')
    reviews = c.fetchall()
    conn.close()
    return render_template_string(reviews_template, reviews=reviews)

if __name__ == '__main__':
    # Run the Flask app in debug mode for testing
    app.run(debug=True)
