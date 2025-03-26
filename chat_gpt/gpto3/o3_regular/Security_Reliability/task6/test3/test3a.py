from flask import Flask, request, render_template_string, redirect, url_for, session, g
import sqlite3, os, uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Ensure this is kept secret in production

DATABASE = 'reviews.db'

def get_db():
    # Use the app context to store the database connection
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.execute('PRAGMA foreign_keys = ON')
    return db

def init_db():
    # Create the reviews table if it doesn't exist
    with app.app_context():
        db = get_db()
        db.execute("DROP TABLE IF EXISTS reviews")
        db.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                review_text TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Generate a CSRF token if one doesn't exist
@app.before_request
def ensure_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = str(uuid.uuid4())

# Simulate a logged-in user for testing purposes
@app.before_request
def simulate_login():
    if 'user_id' not in session:
        session['user_id'] = 1  # In a real app, set this upon user authentication

@app.route('/')
def index():
    # Static product list for testing; assume products exist in your real DB.
    products = [{'id': 1, 'name': 'Product A'}, {'id': 2, 'name': 'Product B'}]
    html = '''
    <h1>Products</h1>
    <ul>
    {% for product in products %}
       <li>
         <a href="{{ url_for('write_review', product_id=product.id) }}">{{ product.name }}</a> |
         <a href="{{ url_for('view_reviews', product_id=product.id) }}">View Reviews</a>
       </li>
    {% endfor %}
    </ul>
    '''
    return render_template_string(html, products=products)

@app.route('/review/<int:product_id>', methods=['GET', 'POST'])
def write_review(product_id):
    error = None
    if request.method == 'POST':
        # Check the CSRF token from the form against the session token
        form_csrf_token = request.form.get('csrf_token')
        if not form_csrf_token or form_csrf_token != session.get('csrf_token'):
            error = "Invalid CSRF token"
        else:
            try:
                rating = int(request.form.get('rating', 0))
                if rating < 1 or rating > 5:
                    error = "Rating must be between 1 and 5."
            except ValueError:
                error = "Invalid rating."
            review_text = request.form.get('review_text', '').strip()
            if not review_text:
                error = "Review text cannot be empty."
        if not error:
            # Use parameterized queries to prevent SQL injection
            db = get_db()
            db.execute('''
                INSERT INTO reviews (product_id, user_id, review_text, rating)
                VALUES (?, ?, ?, ?)
            ''', (product_id, session.get('user_id'), review_text, rating))
            db.commit()
            return redirect(url_for('view_reviews', product_id=product_id))
    # Render the review form with the CSRF token embedded
    html = '''
    <h1>Write a Review for Product {{ product_id }}</h1>
    {% if error %}
      <p style="color:red;">{{ error }}</p>
    {% endif %}
    <form method="post">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <label for="review_text">Review:</label><br>
      <textarea name="review_text" rows="4" cols="50" required></textarea><br><br>
      <label for="rating">Rating (1-5):</label><br>
      <input type="number" name="rating" min="1" max="5" required><br><br>
      <button type="submit">Submit Review</button>
    </form>
    <p><a href="{{ url_for('index') }}">Back to products</a></p>
    '''
    return render_template_string(html, product_id=product_id, csrf_token=session.get('csrf_token'), error=error)

@app.route('/reviews/<int:product_id>')
def view_reviews(product_id):
    db = get_db()
    cur = db.execute('SELECT user_id, review_text, rating, created_at FROM reviews WHERE product_id = ? ORDER BY created_at DESC', (product_id,))
    reviews = cur.fetchall()
    html = '''
    <h1>Reviews for Product {{ product_id }}</h1>
    <a href="{{ url_for('write_review', product_id=product_id) }}">Write a Review</a>
    <ul>
    {% for review in reviews %}
      <li>
         <strong>User {{ review[0] }}</strong> rated: {{ review[2] }}<br>
         {{ review[1] }}<br>
         <em>{{ review[3] }}</em>
      </li>
    {% else %}
       <li>No reviews yet.</li>
    {% endfor %}
    </ul>
    <p><a href="{{ url_for('index') }}">Back to products</a></p>
    '''
    return render_template_string(html, product_id=product_id, reviews=reviews)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
