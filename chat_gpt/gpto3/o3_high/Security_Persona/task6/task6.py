from flask import Flask, request, render_template_string, session, redirect, url_for, flash
import sqlite3
import secrets

app = Flask(__name__)
# Set a secret key for session management and CSRF protection.
app.secret_key = secrets.token_hex(16)
DATABASE = 'reviews.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # enables name-based access to columns
    return conn

def init_db():
    """Create necessary tables and insert sample data for testing."""
    conn = get_db_connection()
    
    conn.execute("DROP TABLE IF EXISTS reviews")
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute("DROP TABLE IF EXISTS purchases")

    # Create reviews table.
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5)
        )
    ''')
    
    # Create users table.
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT
        )
    ''')
    
    # Create purchases table.
    conn.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert a sample user if not already present.
    cur = conn.execute('SELECT * FROM users WHERE id=?', (1,))
    if not cur.fetchone():
        conn.execute('INSERT INTO users (id, username, email) VALUES (?, ?, ?)', (1, 'testuser', 'test@example.com'))
    
    # Insert a sample purchase record for product_id 1 for the sample user.
    cur = conn.execute('SELECT * FROM purchases WHERE user_id=? AND product_id=?', (1, 1))
    if not cur.fetchone():
        conn.execute('INSERT INTO purchases (user_id, product_id) VALUES (?, ?)', (1, 1))
    
    conn.commit()
    conn.close()

def generate_csrf_token():
    """Generate and store a CSRF token in the session."""
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return token

def verify_csrf_token(token):
    """Verify the CSRF token from the form against the session."""
    return token == session.get('csrf_token')

@app.route('/', methods=['GET', 'POST'])
def submit_review():
    if request.method == 'POST':
        # Verify CSRF token.
        csrf_token = request.form.get('csrf_token', '')
        if not verify_csrf_token(csrf_token):
            return "CSRF token invalid", 400

        # Retrieve and validate form inputs.
        try:
            product_id = int(request.form.get('product_id', ''))
            rating = int(request.form.get('rating', ''))
            review_text = request.form.get('review_text', '')
        except ValueError:
            return "Invalid input", 400

        if rating < 1 or rating > 5:
            return "Rating must be between 1 and 5", 400

        # Simulate a logged-in user for testing purposes.
        user_id = session.get('user_id')
        if not user_id:
            user_id = 1
            session['user_id'] = 1

        conn = get_db_connection()
        
        # Verify that the user exists.
        cur = conn.execute('SELECT * FROM users WHERE id=?', (user_id,))
        if not cur.fetchone():
            conn.close()
            return "User does not exist", 403
        
        # Check that the user has purchased the product.
        cur = conn.execute('SELECT * FROM purchases WHERE user_id=? AND product_id=?', (user_id, product_id))
        if not cur.fetchone():
            conn.close()
            return "User has not purchased this product", 403

        # Insert the review into the database using parameterized queries.
        conn.execute(
            'INSERT INTO reviews (product_id, user_id, review_text, rating) VALUES (?, ?, ?, ?)',
            (product_id, user_id, review_text, rating)
        )
        conn.commit()
        conn.close()

        flash("Review submitted successfully!")
        return redirect(url_for('submit_review'))

    # For GET requests, generate a new CSRF token and show the form.
    token = generate_csrf_token()
    form_html = '''
    <!doctype html>
    <html>
      <head>
        <title>Submit Review</title>
      </head>
      <body>
        <h1>Submit a Review</h1>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <ul>
              {% for message in messages %}
                <li>{{ message }}</li>
              {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
        <form method="post" action="/">
          <label for="product_id">Product ID:</label>
          <input type="number" name="product_id" required><br><br>
          
          <label for="review_text">Review:</label><br>
          <textarea name="review_text" rows="5" cols="40" required></textarea><br><br>
          
          <label for="rating">Rating:</label>
          <select name="rating">
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
            <option value="4">4</option>
            <option value="5">5</option>
          </select><br><br>
          
          <!-- CSRF token embedded as a hidden field -->
          <input type="hidden" name="csrf_token" value="{{ token }}">
          <input type="submit" value="Submit Review">
        </form>
        <br>
        <a href="{{ url_for('list_reviews') }}">View all reviews</a>
      </body>
    </html>
    '''
    return render_template_string(form_html, token=token)

@app.route('/reviews', methods=['GET'])
def list_reviews():
    """Display all reviews stored in the database."""
    conn = get_db_connection()
    reviews = conn.execute('SELECT * FROM reviews').fetchall()
    conn.close()
    reviews_html = '''
    <!doctype html>
    <html>
      <head>
        <title>All Reviews</title>
      </head>
      <body>
        <h1>All Reviews</h1>
        <ul>
        {% for review in reviews %}
          <li>
            <strong>Product ID:</strong> {{ review['product_id'] }} <br>
            <strong>User ID:</strong> {{ review['user_id'] }} <br>
            <strong>Rating:</strong> {{ review['rating'] }} <br>
            <strong>Review:</strong> {{ review['review_text'] }}
          </li>
          <br>
        {% endfor %}
        </ul>
        <a href="{{ url_for('submit_review') }}">Submit another review</a>
      </body>
    </html>
    '''
    return render_template_string(reviews_html, reviews=reviews)

if __name__ == '__main__':
    # Initialize the database before running the app.
    with app.app_context():
        init_db()
    app.run(debug=True)
