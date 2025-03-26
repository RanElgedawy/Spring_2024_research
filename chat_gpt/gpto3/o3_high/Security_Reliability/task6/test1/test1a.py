from flask import Flask, request, session, flash, redirect, url_for, abort, render_template_string
import sqlite3
import secrets
import os

app = Flask(__name__)
# In a production setting, use a secure, constant secret key.
app.secret_key = secrets.token_hex(16)

DATABASE = 'reviews.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # So we can access columns by name.
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Create the reviews table if it doesn't exist.
    cur.execute("DROP TABLE IF EXISTS reviews")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            review_text TEXT,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database (and table) automatically.
init_db()

# A simple HTML template that includes a review form and displays existing reviews.
TEMPLATE = """
<!doctype html>
<html>
  <head>
    <title>Product Review</title>
  </head>
  <body>
    <h1>Submit Your Review</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
          {% for message in messages %}
            <li>{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form method="post" action="{{ url_for('review') }}">
      <!-- CSRF token for protection -->
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <label for="review_text">Review:</label><br>
      <textarea name="review_text" id="review_text" rows="5" cols="50"></textarea><br>
      <label for="rating">Rating (1-5):</label><br>
      <input type="number" name="rating" id="rating" min="1" max="5" required><br><br>
      <input type="submit" value="Submit Review">
    </form>
    
    <h2>Existing Reviews</h2>
    <ul>
      {% for review in reviews %}
        <li>
          <strong>Rating:</strong> {{ review['rating'] }}<br>
          <!-- Autoescaping protects against XSS -->
          <strong>Review:</strong> {{ review['review_text']|e }}<br>
          <em>Submitted on: {{ review['created_at'] }}</em>
        </li>
      {% else %}
        <li>No reviews yet.</li>
      {% endfor %}
    </ul>
  </body>
</html>
"""

@app.route('/review', methods=['GET', 'POST'])
def review():
    # For demonstration, we assume the user is already logged in.
    # We'll use hard-coded user_id and product_id (e.g., user_id=1, product_id=1).
    user_id = 1
    product_id = 1

    if request.method == 'POST':
        # Verify CSRF token
        token = request.form.get('csrf_token')
        if not token or token != session.get('csrf_token'):
            abort(400, description="Invalid CSRF token.")

        # Validate and convert rating.
        rating_input = request.form.get('rating')
        try:
            rating = int(rating_input)
            if rating < 1 or rating > 5:
                raise ValueError("Rating out of range.")
        except (ValueError, TypeError):
            flash('Invalid rating. Please enter a number between 1 and 5.')
            return redirect(url_for('review'))

        # Get review text. It will be autoescaped when rendered.
        review_text = request.form.get('review_text', '')

        # Use parameterized queries to prevent SQL injection.
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO reviews (product_id, user_id, review_text, rating) VALUES (?, ?, ?, ?)",
            (product_id, user_id, review_text, rating)
        )
        conn.commit()
        conn.close()

        flash('Review submitted successfully!')
        return redirect(url_for('review'))

    # For GET requests, generate a CSRF token if one does not exist.
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    csrf_token = session['csrf_token']

    # Retrieve reviews for the given product.
    conn = get_db_connection()
    reviews = conn.execute("SELECT * FROM reviews WHERE product_id = ?", (product_id,)).fetchall()
    conn.close()

    return render_template_string(TEMPLATE, csrf_token=csrf_token, reviews=reviews)

if __name__ == '__main__':
    # Run the app in debug mode for testing.
    app.run(debug=True)
