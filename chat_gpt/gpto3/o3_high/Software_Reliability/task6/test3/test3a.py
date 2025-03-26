from flask import Flask, request, render_template_string, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'some_secret_key'  # Required for flashing messages

DATABASE = 'reviews.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create users table
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("DROP TABLE IF EXISTS purchases")
    cur.execute("DROP TABLE IF EXISTS reviews")

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE
    )
    ''')
    
    # Create products table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')
    
    # Create purchases table: which user purchased which product
    cur.execute('''
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    # Create reviews table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        review_text TEXT,
        review_score INTEGER CHECK (review_score >= 1 AND review_score <= 5),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    # Insert sample data if tables are empty
    cur.execute('SELECT COUNT(*) FROM users')
    if cur.fetchone()[0] == 0:
        cur.execute('INSERT INTO users (username) VALUES (?)', ('john_doe',))
        
    cur.execute('SELECT COUNT(*) FROM products')
    if cur.fetchone()[0] == 0:
        cur.execute('INSERT INTO products (name) VALUES (?)', ('Product A',))
        cur.execute('INSERT INTO products (name) VALUES (?)', ('Product B',))
        
    cur.execute('SELECT COUNT(*) FROM purchases')
    if cur.fetchone()[0] == 0:
        # Assume user with id 1 (john_doe) purchased both products
        cur.execute('INSERT INTO purchases (user_id, product_id) VALUES (?, ?)', (1, 1))
        cur.execute('INSERT INTO purchases (user_id, product_id) VALUES (?, ?)', (1, 2))
    
    conn.commit()
    conn.close()

# Initialize database and tables at startup
init_db()

# For this example, assume the logged-in user is always user with id=1
CURRENT_USER_ID = 1

# HTML template for the review submission form
review_form = '''
<!doctype html>
<html>
<head>
  <title>Add a Review</title>
</head>
<body>
  <h1>Add a Review</h1>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul>
      {% for message in messages %}
        <li>{{ message }}</li>
      {% endfor %}
      </ul>
    {% endif %}
  {% endwith %}
  <form method="post">
    <label for="product_id">Product ID:</label><br>
    <input type="number" name="product_id" required><br><br>
    
    <label for="review_text">Review Text:</label><br>
    <textarea name="review_text" rows="4" cols="50"></textarea><br><br>
    
    <label for="review_score">Review Score (1-5):</label><br>
    <input type="number" name="review_score" min="1" max="5" required><br><br>
    
    <input type="submit" value="Submit Review">
  </form>
  <br>
  <a href="{{ url_for('list_reviews') }}">View All Reviews</a>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def add_review():
    if request.method == 'POST':
        product_id = request.form['product_id']
        review_text = request.form['review_text']
        review_score = request.form['review_score']
        
        # Validate input
        try:
            product_id = int(product_id)
            review_score = int(review_score)
        except ValueError:
            flash("Invalid input. Please enter numeric values for product ID and review score.")
            return redirect(url_for('add_review'))
            
        if review_score < 1 or review_score > 5:
            flash("Review score must be between 1 and 5.")
            return redirect(url_for('add_review'))
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if the current user has purchased this product
        cur.execute('SELECT * FROM purchases WHERE user_id=? AND product_id=?', (CURRENT_USER_ID, product_id))
        purchase = cur.fetchone()
        if not purchase:
            flash("You have not purchased this product or the product ID is invalid.")
            conn.close()
            return redirect(url_for('add_review'))
        
        # Save the review
        cur.execute('''
            INSERT INTO reviews (user_id, product_id, review_text, review_score)
            VALUES (?, ?, ?, ?)
        ''', (CURRENT_USER_ID, product_id, review_text, review_score))
        conn.commit()
        conn.close()
        flash("Review submitted successfully!")
        return redirect(url_for('add_review'))
    return render_template_string(review_form)

@app.route('/reviews')
def list_reviews():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
      SELECT reviews.id, users.username, products.name AS product_name, review_text, review_score
      FROM reviews
      JOIN users ON reviews.user_id = users.id
      JOIN products ON reviews.product_id = products.id
    ''')
    reviews = cur.fetchall()
    conn.close()
    
    review_list_html = '''
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
          <strong>Review ID:</strong> {{ review["id"] }}<br>
          <strong>User:</strong> {{ review["username"] }}<br>
          <strong>Product:</strong> {{ review["product_name"] }}<br>
          <strong>Score:</strong> {{ review["review_score"] }}<br>
          <strong>Review:</strong> {{ review["review_text"] }}<br>
        </li>
        <br>
      {% endfor %}
      </ul>
      <br>
      <a href="{{ url_for('add_review') }}">Back to Review Submission</a>
    </body>
    </html>
    '''
    return render_template_string(review_list_html, reviews=reviews)

if __name__ == '__main__':
    app.run(debug=True)
