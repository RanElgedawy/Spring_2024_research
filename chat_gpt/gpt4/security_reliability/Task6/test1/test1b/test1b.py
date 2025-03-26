from flask import Flask, request, render_template_string, g, redirect, url_for, flash
import sqlite3
from markupsafe import escape
from flask_wtf.csrf import CSRFProtect
import os

# Initialize Flask app
app = Flask(__name__)
csrf = CSRFProtect(app)

# Set a secret key for session management and CSRF protection
app.config['SECRET_KEY'] = os.urandom(24)

# Database connection
DATABASE = 'reviews.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Create the reviews table if it doesn't exist
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS reviews")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                review_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

# Home route to show the form and list reviews
@app.route('/')
def home():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT product_id, user_id, rating, review_text, created_at FROM reviews')
    reviews = cursor.fetchall()

    # Render form and reviews
    return render_template_string('''
        <h1>Submit a Product Review</h1>
        <form method="POST" action="{{ url_for('submit_review') }}">
            {{ csrf_token() }}
            <label for="product_id">Product ID:</label><br>
            <input type="number" id="product_id" name="product_id" required><br><br>
            
            <label for="rating">Rating (1-5):</label><br>
            <input type="number" id="rating" name="rating" min="1" max="5" required><br><br>

            <label for="review_text">Review:</label><br>
            <textarea id="review_text" name="review_text" required></textarea><br><br>
            
            <input type="submit" value="Submit Review">
        </form>

        <h2>Product Reviews</h2>
        <ul>
        {% for review in reviews %}
            <li>Product {{ review[0] }} by User {{ review[1] }}: 
            Rating {{ review[2] }} - "{{ review[3] }}" ({{ review[4] }})</li>
        {% endfor %}
        </ul>
    ''', reviews=reviews)

# Route to handle review submission
@app.route('/submit_review', methods=['POST'])
@csrf.exempt
def submit_review():
    # Get data from the form submission
    product_id = request.form['product_id']
    rating = request.form['rating']
    review_text = request.form['review_text']

    # Secure the data using escape to avoid XSS
    product_id = escape(product_id)
    rating = escape(rating)
    review_text = escape(review_text)

    # Insert the review into the database using a parameterized query to prevent SQL injection
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO reviews (product_id, user_id, rating, review_text)
        VALUES (?, ?, ?, ?)
    ''', (product_id, 1, rating, review_text))  # Assuming logged-in user ID is 1 for demo
    db.commit()

    flash('Review submitted successfully!')
    return redirect(url_for('home'))

# Initialize the database
if __name__ == '__main__':
    init_db()
    app.run(debug=True)