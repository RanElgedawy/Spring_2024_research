from flask import Flask, request, render_template_string, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret_key_for_flashing_messages'

# Name of the SQLite database file
DATABASE = 'ecommerce.db'

# Simulated current logged-in user id
CURRENT_USER_ID = 1

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allow dictionary-like access to rows
    return conn

def init_db():
    """Initialize the database, creating tables if they do not exist and inserting dummy purchase data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create table for products purchased by users
    cursor.execute("DROP TABLE IF EXISTS purchased_products")
    cursor.execute("DROP TABLE IF EXISTS reviews")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchased_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL
        );
    ''')
    
    # Create table for reviews
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            review_score INTEGER NOT NULL CHECK(review_score BETWEEN 1 AND 5)
        );
    ''')
    
    # Insert dummy data for purchased products if table is empty.
    # For testing, we assume CURRENT_USER_ID (1) purchased product IDs 101 and 102.
    cursor.execute('SELECT COUNT(*) FROM purchased_products')
    if cursor.fetchone()[0] == 0:
        dummy_purchases = [(CURRENT_USER_ID, 101), (CURRENT_USER_ID, 102)]
        cursor.executemany('INSERT INTO purchased_products (user_id, product_id) VALUES (?, ?)', dummy_purchases)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    # Redirect to review form for simplicity
    return redirect(url_for('add_review'))

@app.route('/review', methods=['GET', 'POST'])
def add_review():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        review_text = request.form.get('review_text')
        review_score = request.form.get('review_score')
        
        # Basic validation
        if not product_id or not review_text or not review_score:
            flash("Please fill all fields.")
            return redirect(url_for('add_review'))
        
        try:
            product_id = int(product_id)
            review_score = int(review_score)
        except ValueError:
            flash("Product ID and Review Score must be valid numbers.")
            return redirect(url_for('add_review'))
        
        if review_score < 1 or review_score > 5:
            flash("Review score must be between 1 and 5.")
            return redirect(url_for('add_review'))
        
        # Verify that the current user has purchased the product
        cursor.execute('SELECT * FROM purchased_products WHERE user_id=? AND product_id=?', (CURRENT_USER_ID, product_id))
        if not cursor.fetchone():
            flash("You haven't purchased this product.")
            return redirect(url_for('add_review'))
        
        # Save the review into the database
        cursor.execute('''
            INSERT INTO reviews (user_id, product_id, review_text, review_score)
            VALUES (?, ?, ?, ?)
        ''', (CURRENT_USER_ID, product_id, review_text, review_score))
        conn.commit()
        flash("Review added successfully!")
        return redirect(url_for('list_reviews'))
    
    # For GET request, display the form and list purchased products for testing
    cursor.execute('SELECT product_id FROM purchased_products WHERE user_id=?', (CURRENT_USER_ID,))
    purchased_products = cursor.fetchall()
    conn.close()
    purchased_list = ', '.join(str(row['product_id']) for row in purchased_products)
    
    form_html = '''
    <!doctype html>
    <html>
      <head>
        <title>Add Review</title>
      </head>
      <body>
        <h1>Add a Review</h1>
        <p>You have purchased the following products: {{ purchased_list }}</p>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <ul style="color: red;">
            {% for message in messages %}
              <li>{{ message }}</li>
            {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
        <form method="POST">
          <label for="product_id">Product ID:</label><br>
          <input type="text" id="product_id" name="product_id" placeholder="e.g., 101"><br><br>
          <label for="review_text">Review Text:</label><br>
          <textarea id="review_text" name="review_text" placeholder="Enter your review here"></textarea><br><br>
          <label for="review_score">Review Score (1-5):</label><br>
          <input type="number" id="review_score" name="review_score" min="1" max="5"><br><br>
          <input type="submit" value="Submit Review">
        </form>
        <br>
        <a href="{{ url_for('list_reviews') }}">View Your Reviews</a>
      </body>
    </html>
    '''
    return render_template_string(form_html, purchased_list=purchased_list)

@app.route('/reviews')
def list_reviews():
    """Display all reviews added by the current user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reviews WHERE user_id=?', (CURRENT_USER_ID,))
    reviews = cursor.fetchall()
    conn.close()
    
    reviews_html = '''
    <!doctype html>
    <html>
      <head>
        <title>Your Reviews</title>
      </head>
      <body>
        <h1>Your Reviews</h1>
        {% if reviews %}
          <ul>
          {% for review in reviews %}
            <li>
              <strong>Product {{ review["product_id"] }}</strong> - Score: {{ review["review_score"] }}<br>
              {{ review["review_text"] }}
            </li>
          {% endfor %}
          </ul>
        {% else %}
          <p>You haven't added any reviews yet.</p>
        {% endif %}
        <a href="{{ url_for('add_review') }}">Add another review</a>
      </body>
    </html>
    '''
    return render_template_string(reviews_html, reviews=reviews)

if __name__ == '__main__':
    # Initialize the database if it doesn't exist
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
