from flask import Flask, render_template_string, request, redirect, url_for, session, flash, g
import sqlite3
import os
import secrets

app = Flask(__name__)
app.secret_key = os.urandom(32)  # Used for sessions and CSRF protection

DATABASE = 'reviews.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Automatically create the reviews table if it does not exist."""
    db = get_db()
    db.execute("DROP TABLE IF EXISTS reviews")
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            rating INTEGER,
            review_text TEXT
        )
    ''')
    db.commit()

@app.before_request
def before_request():
    init_db()
    # Set a CSRF token in session if not present
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)

# HTML template for review submission and display
review_template = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Leave a Review</title>
</head>
<body>
  <h1>Leave a Review</h1>
  <form method="post" action="{{ url_for('leave_review') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <label for="product_id">Product ID:</label><br>
    <input type="number" name="product_id" id="product_id" required><br><br>
    
    <label for="rating">Rating (1-5):</label><br>
    <input type="number" name="rating" id="rating" min="1" max="5" required><br><br>
    
    <label for="review_text">Review:</label><br>
    <textarea name="review_text" id="review_text" rows="5" cols="40" required></textarea><br><br>
    
    <button type="submit">Submit Review</button>
  </form>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul>
      {% for message in messages %}
        <li>{{ message }}</li>
      {% endfor %}
      </ul>
    {% endif %}
  {% endwith %}
  
  <h2>Existing Reviews</h2>
  {% for review in reviews %}
    <div>
      <strong>Product ID:</strong> {{ review['product_id'] }}<br>
      <strong>Rating:</strong> {{ review['rating'] }}<br>
      <strong>Review:</strong> {{ review['review_text'] | e }}<br>
    </div>
    <hr>
  {% endfor %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def leave_review():
    if request.method == 'POST':
        # Validate CSRF token
        if request.form.get('csrf_token') != session.get('csrf_token'):
            flash("Invalid CSRF token!")
            return redirect(url_for('leave_review'))
        
        try:
            product_id = int(request.form.get('product_id'))
            rating = int(request.form.get('rating'))
            review_text = request.form.get('review_text')
        except (ValueError, TypeError):
            flash("Invalid input!")
            return redirect(url_for('leave_review'))
        
        if rating < 1 or rating > 5:
            flash("Rating must be between 1 and 5!")
            return redirect(url_for('leave_review'))
        
        db = get_db()
        # Use parameterized query to protect against SQL injection
        db.execute("INSERT INTO reviews (user_id, product_id, rating, review_text) VALUES (?, ?, ?, ?)",
                   (1, product_id, rating, review_text))
        db.commit()
        flash("Review submitted successfully!")
        return redirect(url_for('leave_review'))
    
    # Retrieve and display all reviews
    db = get_db()
    cur = db.execute("SELECT product_id, rating, review_text FROM reviews")
    reviews = cur.fetchall()
    return render_template_string(review_template, csrf_token=session.get('csrf_token'), reviews=reviews)

if __name__ == '__main__':
    app.run(debug=True)
