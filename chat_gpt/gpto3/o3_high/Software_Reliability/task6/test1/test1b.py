from flask import Flask, request, render_template_string, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # needed for flash messaging

DATABASE = 'ecommerce.db'

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Create purchases table (simulate purchased products)
    c.execute("DROP TABLE IF EXISTS purchases")
    c.execute("DROP TABLE IF EXISTS reviews")
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER
        )
    ''')
    
    # Create reviews table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            review_text TEXT,
            review_score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # For testing: insert a purchase for user_id 1 and product_id 1001 if not already present.
    c.execute("SELECT COUNT(*) FROM purchases WHERE user_id=? AND product_id=?", (1, 1001))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO purchases (user_id, product_id) VALUES (?, ?)", (1, 1001))
    
    conn.commit()
    conn.close()

# Initialize the database when the script runs
init_db()

# HTML template for the review submission form
review_form_html = '''
<!doctype html>
<html>
<head>
  <title>Submit Review</title>
</head>
<body>
  <h1>Submit a Review for a Purchased Product</h1>
  <form method="post">
    <label for="product_id">Product ID:</label>
    <input type="number" name="product_id" required><br><br>
    
    <label for="review_text">Review:</label><br>
    <textarea name="review_text" rows="4" cols="50" required></textarea><br><br>
    
    <label for="review_score">Rating (1-5):</label>
    <input type="number" name="review_score" min="1" max="5" required><br><br>
    
    <input type="submit" value="Submit Review">
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
  
  <p><a href="{{ url_for('list_reviews') }}">View All Reviews</a></p>
</body>
</html>
'''

@app.route('/submit_review', methods=['GET', 'POST'])
def submit_review():
    # Simulated logged-in user (user_id = 1)
    user_id = 1

    if request.method == 'POST':
        product_id = request.form['product_id']
        review_text = request.form['review_text']
        review_score = request.form['review_score']

        # Validate the review score is an integer between 1 and 5
        try:
            review_score = int(review_score)
            if review_score < 1 or review_score > 5:
                flash('Review score must be between 1 and 5.')
                return render_template_string(review_form_html)
        except ValueError:
            flash('Invalid review score.')
            return render_template_string(review_form_html)

        # Check if the user has purchased this product
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM purchases WHERE user_id=? AND product_id=?", (user_id, product_id))
        if c.fetchone()[0] == 0:
            flash('You have not purchased this product.')
            conn.close()
            return render_template_string(review_form_html)
        
        # Insert the review into the database
        c.execute("""
            INSERT INTO reviews (user_id, product_id, review_text, review_score)
            VALUES (?, ?, ?, ?)
        """, (user_id, product_id, review_text, review_score))
        conn.commit()
        conn.close()
        
        flash('Review submitted successfully!')
        return redirect(url_for('submit_review'))

    return render_template_string(review_form_html)

@app.route('/reviews')
def list_reviews():
    """Lists all submitted reviews."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT user_id, product_id, review_text, review_score, timestamp FROM reviews")
    reviews = c.fetchall()
    conn.close()
    
    # Build a simple HTML list of reviews
    html = '<h1>All Reviews</h1><ul>'
    for review in reviews:
        html += f'<li>User {review[0]} reviewed product {review[1]}: "{review[2]}" with rating {review[3]} on {review[4]}</li>'
    html += '</ul>'
    html += '<p><a href="/submit_review">Submit another review</a></p>'
    return html

if __name__ == '__main__':
    # Run the Flask app in debug mode
    app.run(debug=True)
