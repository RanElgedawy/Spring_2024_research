from flask import Flask, request, render_template_string, redirect, url_for, session, flash
import sqlite3
import os
import secrets
from datetime import datetime

app = Flask(__name__)
# Set a secret key for session management and CSRF protection
app.secret_key = secrets.token_hex(16)
DATABASE = 'reviews.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database and create tables if they do not exist."""
    with get_db_connection() as conn:
        # Create products table (dummy product for testing)
        conn.execute("DROP TABLE IF EXISTS products")
        conn.execute("DROP TABLE IF EXISTS reviews")

        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            )
        ''')
        # Create reviews table with a constraint on rating to be between 1 and 5.
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                review_text TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        # Insert a dummy product if the table is empty.
        cur = conn.execute('SELECT COUNT(*) FROM products')
        count = cur.fetchone()[0]
        if count == 0:
            conn.execute("INSERT INTO products (name, description) VALUES (?, ?)",
                         ("Sample Product", "A sample product for testing."))
        conn.commit()

@app.before_first_request
def setup():
    init_db()

@app.route('/login')
def login():
    """
    Dummy login route.
    In a real application, you would implement proper authentication.
    Here we simply set a dummy user_id in the session.
    """
    session['user_id'] = 1
    flash("You are now logged in as user 1.")
    return redirect(url_for('list_products'))

@app.route('/products')
def list_products():
    """
    List available products.
    For each product, a link is provided to write a review.
    """
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    template = '''
    <h1>Products</h1>
    <ul>
      {% for product in products %}
        <li>
          {{ product['name'] }} - 
          <a href="{{ url_for('submit_review', product_id=product['id']) }}">Write a Review</a>
        </li>
      {% endfor %}
    </ul>
    <p><a href="{{ url_for('view_reviews') }}">View all reviews</a></p>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
          {% for message in messages %}
            <li>{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    '''
    return render_template_string(template, products=products)

@app.route('/review/<int:product_id>', methods=['GET', 'POST'])
def submit_review(product_id):
    """
    Allows a logged-in user to submit a review for a specific product.
    Implements CSRF protection and input validation.
    """
    if 'user_id' not in session:
        flash("You must be logged in to submit a review.")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product is None:
        return "Product not found", 404

    if request.method == 'POST':
        # Verify CSRF token to protect against CSRF attacks
        token = request.form.get('csrf_token')
        if not token or token != session.get('csrf_token'):
            return "Invalid CSRF token", 400
        # Remove CSRF token to prevent reuse
        session.pop('csrf_token', None)
        
        review_text = request.form.get('review_text', '')
        rating = request.form.get('rating')
        try:
            rating = int(rating)
        except (ValueError, TypeError):
            flash("Invalid rating. Please provide a number between 1 and 5.")
            return redirect(request.url)
        
        if rating < 1 or rating > 5:
            flash("Rating must be between 1 and 5.")
            return redirect(request.url)
        
        # Use parameterized queries to protect against SQL injection
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO reviews (product_id, user_id, rating, review_text, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, session['user_id'], rating, review_text, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        flash("Review submitted successfully!")
        return redirect(url_for('list_products'))
    else:
        # Generate a CSRF token on GET request and store it in session
        csrf_token = secrets.token_hex(16)
        session['csrf_token'] = csrf_token
        form_html = '''
        <h1>Write a Review for "{{ product['name'] }}"</h1>
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label for="review_text">Review:</label><br>
            <textarea name="review_text" id="review_text" rows="4" cols="50"></textarea><br>
            <label for="rating">Rating (1-5):</label><br>
            <input type="number" name="rating" id="rating" min="1" max="5" required><br><br>
            <input type="submit" value="Submit Review">
        </form>
        <p><a href="{{ url_for('list_products') }}">Back to products</a></p>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <ul>
              {% for message in messages %}
                <li>{{ message }}</li>
              {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
        '''
        return render_template_string(form_html, product=product, csrf_token=csrf_token)

@app.route('/reviews')
def view_reviews():
    """
    Displays all reviews along with their associated product names.
    """
    conn = get_db_connection()
    reviews = conn.execute('''
        SELECT r.*, p.name as product_name 
        FROM reviews r 
        JOIN products p ON r.product_id = p.id 
        ORDER BY r.created_at DESC
    ''').fetchall()
    conn.close()
    template = '''
    <h1>All Reviews</h1>
    <ul>
      {% for review in reviews %}
        <li>
          <strong>Product:</strong> {{ review['product_name'] }}<br>
          <strong>User ID:</strong> {{ review['user_id'] }}<br>
          <strong>Rating:</strong> {{ review['rating'] }}<br>
          <strong>Review:</strong> {{ review['review_text'] }}<br>
          <strong>Submitted at:</strong> {{ review['created_at'] }}
        </li>
        <hr>
      {% endfor %}
    </ul>
    <p><a href="{{ url_for('list_products') }}">Back to products</a></p>
    '''
    return render_template_string(template, reviews=reviews)

if __name__ == '__main__':
    app.run(debug=True)
