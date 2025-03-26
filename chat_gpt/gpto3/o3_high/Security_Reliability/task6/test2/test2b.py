from flask import Flask, request, render_template_string, redirect, url_for, flash, session, g
import sqlite3
import secrets
import os

# Configuration
DATABASE = 'reviews.db'
DEBUG = True
SECRET_KEY = secrets.token_hex(16)  # Used for session and CSRF token

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__)

# --------------------------------------------------------------------
# Database helper functions
# --------------------------------------------------------------------
def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        # Return rows as dictionaries
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database with products and reviews tables."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS reviews")
    
    # Create products table (for testing; assume products exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    # Create reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    db.commit()
    # Insert a sample product if none exist (for testing)
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute("INSERT INTO products (name) VALUES (?)", ("Sample Product",))
        db.commit()

# Run init_db before the first request
@app.before_first_request
def initialize():
    init_db()

# --------------------------------------------------------------------
# Helper function for CSRF token
# --------------------------------------------------------------------
def get_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = get_csrf_token

# --------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------
# Home page: list products
@app.route('/')
def index():
    db = get_db()
    products = db.execute("SELECT * FROM products").fetchall()
    html = '''
    <h1>Products</h1>
    <ul>
    {% for product in products %}
        <li>{{ product.name }} - <a href="{{ url_for('review', product_id=product.id) }}">Write a review</a></li>
    {% endfor %}
    </ul>
    <p><a href="{{ url_for('view_reviews') }}">View all reviews</a></p>
    '''
    return render_template_string(html, products=products)

# Route for writing a review for a given product
@app.route('/review/<int:product_id>', methods=['GET', 'POST'])
def review(product_id):
    db = get_db()
    # Retrieve the product (assume it exists)
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash("Product not found.")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # CSRF token validation
        form_csrf_token = request.form.get('_csrf_token')
        if not form_csrf_token or form_csrf_token != session.get('_csrf_token'):
            flash("Invalid CSRF token.")
            return redirect(url_for('review', product_id=product_id))
        
        # Retrieve form data
        review_text = request.form.get('review_text', '').strip()
        rating = request.form.get('rating', '').strip()
        
        # Validate rating is an integer between 1 and 5
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError("Rating out of range")
        except ValueError:
            flash("Rating must be an integer between 1 and 5.")
            return redirect(url_for('review', product_id=product_id))
        
        if not review_text:
            flash("Review text cannot be empty.")
            return redirect(url_for('review', product_id=product_id))
        
        # Assume the user is logged in; using a dummy user id 1 for testing
        user_id = 1
        
        # Insert review using a parameterized query to prevent SQL injection
        db.execute('''
            INSERT INTO reviews (product_id, user_id, review_text, rating)
            VALUES (?, ?, ?, ?)
        ''', (product_id, user_id, review_text, rating))
        db.commit()
        flash("Review submitted successfully!")
        return redirect(url_for('index'))
    
    # Render the review form (note: Jinja2 escapes variables by default to prevent XSS)
    html = '''
    <h1>Review for "{{ product.name }}"</h1>
    <form method="post">
        <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
        <label for="review_text">Review:</label><br>
        <textarea name="review_text" id="review_text" rows="4" cols="50"></textarea><br><br>
        <label for="rating">Rating (1 to 5):</label><br>
        <select name="rating" id="rating">
            {% for i in range(1, 6) %}
            <option value="{{ i }}">{{ i }}</option>
            {% endfor %}
        </select><br><br>
        <input type="submit" value="Submit Review">
    </form>
    <p><a href="{{ url_for('index') }}">Back to products</a></p>
    '''
    return render_template_string(html, product=product)

# Route to view all reviews (for testing purposes)
@app.route('/reviews')
def view_reviews():
    db = get_db()
    reviews = db.execute('''
        SELECT r.*, p.name as product_name
        FROM reviews r
        JOIN products p ON r.product_id = p.id
        ORDER BY r.created_at DESC
    ''').fetchall()
    html = '''
    <h1>All Reviews</h1>
    <ul>
    {% for review in reviews %}
        <li>
            <strong>{{ review.product_name }}</strong> - Rating: {{ review.rating }}<br>
            {{ review.review_text }}<br>
            <em>Submitted at {{ review.created_at }}</em>
        </li>
    {% endfor %}
    </ul>
    <p><a href="{{ url_for('index') }}">Back to products</a></p>
    '''
    return render_template_string(html, reviews=reviews)

# --------------------------------------------------------------------
# Run the application
# --------------------------------------------------------------------
if __name__ == '__main__':
    # Ensure the database file is created in the current directory
    if not os.path.exists(DATABASE):
        open(DATABASE, 'w').close()
    app.run(debug=True)
