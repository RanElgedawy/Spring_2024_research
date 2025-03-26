from flask import Flask, request, render_template_string, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flashing messages

DATABASE = 'reviews.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create tables for users, purchases, and reviews
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS purchases")
    cur.execute("DROP TABLE IF EXISTS reviews")

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            purchase_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            review_score INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Insert sample data for testing (simulate logged-in user and purchased product)
    cur.execute('INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)', (1, 'testuser'))
    cur.execute('INSERT OR IGNORE INTO purchases (id, user_id, product_id, purchase_date) VALUES (?, ?, ?, ?)', 
                (1, 1, 1001, '2023-01-01'))
    conn.commit()
    conn.close()

@app.route('/add_review', methods=['GET'])
def add_review():
    # For testing, we simulate a logged in user with user_id = 1.
    form_html = '''
    <h1>Add Product Review</h1>
    <form action="{{ url_for('submit_review') }}" method="post">
        <label for="product_id">Product ID:</label>
        <input type="number" name="product_id" required><br><br>
        <label for="review_text">Review:</label><br>
        <textarea name="review_text" rows="5" cols="40" required></textarea><br><br>
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
    <p><a href="{{ url_for('reviews') }}">View all reviews</a></p>
    '''
    return render_template_string(form_html)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    user_id = 1  # Simulated logged-in user id
    product_id = request.form.get('product_id')
    review_text = request.form.get('review_text')
    review_score = request.form.get('review_score')
    
    # Validate inputs
    try:
        product_id = int(product_id)
        review_score = int(review_score)
        if review_score < 1 or review_score > 5:
            flash("Rating must be between 1 and 5.")
            return redirect(url_for('add_review'))
    except ValueError:
        flash("Invalid input. Please enter valid numbers.")
        return redirect(url_for('add_review'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if the user has purchased the product
    cur.execute('SELECT * FROM purchases WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    purchase = cur.fetchone()
    if not purchase:
        flash("You have not purchased this product.")
        conn.close()
        return redirect(url_for('add_review'))
    
    # Insert the review into the database
    cur.execute('INSERT INTO reviews (user_id, product_id, review_text, review_score) VALUES (?, ?, ?, ?)',
                (user_id, product_id, review_text, review_score))
    conn.commit()
    conn.close()
    
    flash("Review submitted successfully!")
    return redirect(url_for('add_review'))

@app.route('/reviews', methods=['GET'])
def reviews():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM reviews')
    all_reviews = cur.fetchall()
    conn.close()
    
    review_html = '''
    <h1>All Reviews</h1>
    <ul>
    {% for review in reviews %}
      <li>
        <strong>User ID:</strong> {{ review['user_id'] }}, 
        <strong>Product ID:</strong> {{ review['product_id'] }}, 
        <strong>Rating:</strong> {{ review['review_score'] }}<br>
        <strong>Review:</strong> {{ review['review_text'] }}
      </li>
    {% endfor %}
    </ul>
    <p><a href="{{ url_for('add_review') }}">Add another review</a></p>
    '''
    return render_template_string(review_html, reviews=all_reviews)

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
