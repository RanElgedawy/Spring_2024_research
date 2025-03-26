from flask import Flask, request, render_template_string, redirect, url_for, session, flash
import sqlite3
import os
import secrets

app = Flask(__name__)
# A secure random secret key for sessions (in production, store this securely)
app.secret_key = secrets.token_hex(16)

DATABASE = 'reviews.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create reviews table if it doesn't exist."""
    with get_db_connection() as conn:
        conn.execute("DROP TABLE IF EXISTS reviews")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                review_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# Initialize the DB on startup
init_db()

# Template for the review form
review_form_template = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Leave a Review</title>
</head>
<body>
  <h1>Review for Product {{ product_id }}</h1>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul>
      {% for message in messages %}
        <li>{{ message }}</li>
      {% endfor %}
      </ul>
    {% endif %}
  {% endwith %}
  <form method="POST" action="{{ url_for('submit_review', product_id=product_id) }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <label for="rating">Rating (1-5):</label>
    <input type="number" name="rating" min="1" max="5" required><br><br>
    <label for="review_text">Review:</label><br>
    <textarea name="review_text" rows="5" cols="40" required></textarea><br><br>
    <button type="submit">Submit Review</button>
  </form>
  <p><a href="{{ url_for('view_reviews', product_id=product_id) }}">View Reviews</a></p>
</body>
</html>
"""

# Template for displaying reviews
reviews_template = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Reviews for Product {{ product_id }}</title>
</head>
<body>
  <h1>Reviews for Product {{ product_id }}</h1>
  {% if reviews %}
    <ul>
      {% for review in reviews %}
        <li>
          <strong>Rating:</strong> {{ review['rating'] }}<br>
          <strong>Review:</strong> {{ review['review_text'] }}<br>
          <em>Submitted on {{ review['created_at'] }}</em>
        </li>
      {% endfor %}
    </ul>
  {% else %}
    <p>No reviews yet.</p>
  {% endif %}
  <p><a href="{{ url_for('review_form', product_id=product_id) }}">Leave a Review</a></p>
</body>
</html>
"""

@app.before_request
def set_csrf_token():
    # Generate a CSRF token for the session if not already present
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)

@app.route('/product/<int:product_id>/review', methods=['GET'])
def review_form(product_id):
    # Render the review form with CSRF token
    return render_template_string(review_form_template, product_id=product_id, csrf_token=session['csrf_token'])

@app.route('/product/<int:product_id>/review', methods=['POST'])
def submit_review(product_id):
    # CSRF token validation
    form_token = request.form.get('csrf_token')
    if not form_token or form_token != session.get('csrf_token'):
        flash("Invalid CSRF token.")
        return redirect(url_for('review_form', product_id=product_id))
    
    # Get and validate form data
    try:
        rating = int(request.form.get('rating', 0))
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5.")
    except ValueError as e:
        flash(str(e))
        return redirect(url_for('review_form', product_id=product_id))
    
    review_text = request.form.get('review_text', '').strip()
    if not review_text:
        flash("Review text cannot be empty.")
        return redirect(url_for('review_form', product_id=product_id))
    
    # In a real application, use the actual logged in user's ID
    # Here we assume a fixed user_id for testing purposes
    user_id = 1

    # Use parameterized queries to prevent SQL injection
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO reviews (product_id, user_id, rating, review_text)
            VALUES (?, ?, ?, ?)
        ''', (product_id, user_id, rating, review_text))
        conn.commit()
    
    flash("Review submitted successfully!")
    return redirect(url_for('review_form', product_id=product_id))

@app.route('/product/<int:product_id>/reviews', methods=['GET'])
def view_reviews(product_id):
    # Fetch reviews for the given product securely
    with get_db_connection() as conn:
        reviews = conn.execute('''
            SELECT rating, review_text, created_at FROM reviews
            WHERE product_id = ?
            ORDER BY created_at DESC
        ''', (product_id,)).fetchall()
    return render_template_string(reviews_template, product_id=product_id, reviews=reviews)

if __name__ == '__main__':
    # Run the app for testing
    app.run(debug=True)
