from flask import Flask, request, render_template_string, redirect, url_for, session, g, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import re
import os
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = os.urandom(24)
csrf = CSRFProtect(app)

DATABASE = 'reviews.db'

# Database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize the database (called during the first request)
def init_db():
    db = get_db()
    db.execute("DROP TABLE IF EXISTS reviews")
    db.execute("DROP TABLE IF EXISTS purchases")
    db.execute('''CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                    review_text TEXT NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL)''')
    db.execute("INSERT INTO purchases (user_id, product_id) VALUES (1, 101), (1, 102);")
    db.commit()

# Flag to check if the database has been initialized
db_initialized = False

@app.before_request
def ensure_db_initialized():
    global db_initialized
    if not db_initialized:
        init_db()
        db_initialized = True

# Check if user has purchased the product
def user_has_purchased_product(user_id, product_id):
    db = get_db()
    purchase = db.execute('SELECT * FROM purchases WHERE user_id = ? AND product_id = ?', 
                          (user_id, product_id)).fetchone()
    return purchase is not None

# Route to submit a review
@app.route('/submit_review', methods=['GET', 'POST'])
@csrf.exempt
def submit_review():
    if request.method == 'POST':
        user_id = session.get('user_id', 1)  # Assuming a logged-in user with ID 1
        product_id = request.form.get('product_id')
        rating = request.form.get('rating')
        review_text = request.form.get('review_text')

        # Validate input
        if not product_id or not product_id.isdigit():
            flash('Product ID is required and must be a valid number.')
            return redirect(url_for('submit_review'))

        if not rating or not rating.isdigit() or int(rating) < 1 or int(rating) > 5:
            flash('Rating is required and must be a number between 1 and 5.')
            return redirect(url_for('submit_review'))

        if not review_text or review_text.strip() == '':
            flash('Review text is required.')
            return redirect(url_for('submit_review'))

        # Check if the user has purchased the product
        if not user_has_purchased_product(user_id, product_id):
            flash('You can only review products you have purchased.')
            return redirect(url_for('submit_review'))

        # Sanitize input
        sanitized_review_text = re.sub(r'[<>]', '', review_text)  # Basic XSS prevention

        # Save to database
        db = get_db()
        db.execute('INSERT INTO reviews (user_id, product_id, rating, review_text) VALUES (?, ?, ?, ?)',
                   (user_id, product_id, rating, sanitized_review_text))
        db.commit()

        flash('Review submitted successfully!')
        return redirect(url_for('submit_review'))

    return render_template_string('''
        <h1>Submit a Review</h1>
        <form method="POST" action="/submit_review">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <label for="product_id">Product ID:</label>
            <input type="text" name="product_id" required><br><br>
            <label for="rating">Rating (1-5):</label>
            <input type="number" name="rating" min="1" max="5" required><br><br>
            <label for="review_text">Review:</label><br>
            <textarea name="review_text" rows="4" cols="50" required></textarea><br><br>
            <input type="submit" value="Submit Review">
        </form>
        <br>
        <a href="/view_reviews">View All Reviews</a>
    ''')

# Route to view all reviews
@app.route('/view_reviews')
def view_reviews():
    db = get_db()
    reviews = db.execute('SELECT * FROM reviews').fetchall()
    return render_template_string('''
        <h1>All Reviews</h1>
        <table border="1">
            <tr><th>ID</th><th>User ID</th><th>Product ID</th><th>Rating</th><th>Review</th></tr>
            {% for review in reviews %}
            <tr>
                <td>{{ review.id }}</td>
                <td>{{ review.user_id }}</td>
                <td>{{ review.product_id }}</td>
                <td>{{ review.rating }}</td>
                <td>{{ review.review_text }}</td>
            </tr>
            {% endfor %}
        </table>
        <br>
        <a href="/submit_review">Submit Another Review</a>
    ''', reviews=reviews)

if __name__ == '__main__':
    app.run(debug=True)