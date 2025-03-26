from flask import Flask, request, render_template_string, session, redirect, url_for, flash
import sqlite3
import os
import secrets

app = Flask(__name__)
# Set a secret key for session management and CSRF protection
app.secret_key = secrets.token_hex(16)

DATABASE = 'reviews.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Create the reviews table if it doesn't exist.
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS reviews")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5)
        )
    ''')
    conn.commit()
    conn.close()

@app.before_first_request
def initialize():
    init_db()

def generate_csrf_token():
    # Generate a CSRF token and store it in the session if it doesn't exist.
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

# Make the CSRF token available in all Jinja templates.
app.jinja_env.globals['csrf_token'] = generate_csrf_token

# HTML template for the review form.
review_form = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Submit Review</title>
</head>
<body>
  <h1>Submit Review for Product {{ product_id }}</h1>
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
    <!-- CSRF protection -->
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    
    <label for="review_text">Review:</label><br>
    <textarea name="review_text" id="review_text" rows="4" cols="50"></textarea><br><br>
    
    <label for="rating">Rating (1-5):</label><br>
    <input type="number" name="rating" id="rating" min="1" max="5"><br><br>
    
    <button type="submit">Submit Review</button>
  </form>
  <br>
  <a href="{{ url_for('list_reviews', product_id=product_id) }}">View Reviews</a>
</body>
</html>
'''

# HTML template to list reviews.
reviews_list = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Reviews for Product {{ product_id }}</title>
</head>
<body>
  <h1>Reviews for Product {{ product_id }}</h1>
  {% for review in reviews %}
    <div style="border: 1px solid #ccc; padding: 10px; margin:10px;">
      <p><strong>User ID:</strong> {{ review.user_id }}</p>
      <p><strong>Rating:</strong> {{ review.rating }}</p>
      <p><strong>Review:</strong> {{ review.review_text }}</p>
    </div>
  {% else %}
    <p>No reviews yet.</p>
  {% endfor %}
  <br>
  <a href="{{ url_for('show_review_form', product_id=product_id) }}">Submit a Review</a>
</body>
</html>
'''

@app.route('/review/<int:product_id>', methods=['GET'])
def show_review_form(product_id):
    # Display the review submission form.
    return render_template_string(review_form, product_id=product_id)

@app.route('/review/<int:product_id>', methods=['POST'])
def submit_review(product_id):
    # Validate CSRF token.
    token = session.get('_csrf_token', None)
    form_token = request.form.get('csrf_token')
    if not token or token != form_token:
        flash('Invalid CSRF token')
        return redirect(url_for('show_review_form', product_id=product_id))
    
    review_text = request.form.get('review_text', '').strip()
    rating = request.form.get('rating', '').strip()
    
    # Validate required fields.
    if not review_text or not rating:
        flash('Review text and rating are required.')
        return redirect(url_for('show_review_form', product_id=product_id))
    
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5.')
            return redirect(url_for('show_review_form', product_id=product_id))
    except ValueError:
        flash('Invalid rating value.')
        return redirect(url_for('show_review_form', product_id=product_id))
    
    # In a real application, user_id would be fetched from the logged-in session.
    user_id = 1  # Placeholder user ID.
    
    # Use parameterized queries to prevent SQL injection.
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO reviews (product_id, user_id, review_text, rating) VALUES (?, ?, ?, ?)',
        (product_id, user_id, review_text, rating)
    )
    conn.commit()
    conn.close()
    
    flash('Review submitted successfully!')
    return redirect(url_for('show_review_form', product_id=product_id))

@app.route('/reviews/<int:product_id>')
def list_reviews(product_id):
    # Retrieve reviews for a specific product.
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,))
    reviews = cursor.fetchall()
    conn.close()
    return render_template_string(reviews_list, reviews=reviews, product_id=product_id)

if __name__ == '__main__':
    # Run the app in debug mode for testing.
    app.run(debug=True)
