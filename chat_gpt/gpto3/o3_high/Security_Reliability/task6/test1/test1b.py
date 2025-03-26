from flask import Flask, request, session, render_template_string, redirect, url_for
import sqlite3
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Needed for session management and CSRF protection
DATABASE = 'reviews.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # To access columns by name
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create products table (assume products already exist in production)

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')
    # Create reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            review_text TEXT,
            rating INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    # Insert a sample product if none exist for testing
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO products (name, description) VALUES (?, ?)', 
                       ("Sample Product", "This is a sample product for testing reviews."))
    conn.commit()
    conn.close()

@app.before_request
def before_request():
    # For testing purposes, assume the user is logged in with user_id 1.
    session.setdefault('user_id', 1)

def generate_csrf_token():
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return token

# Templates defined inline
INDEX_TEMPLATE = '''
<!doctype html>
<title>Products</title>
<h1>Products</h1>
<ul>
  {% for product in products %}
    <li>
      <a href="{{ url_for('product_detail', product_id=product.id) }}">{{ product.name }}</a>
    </li>
  {% endfor %}
</ul>
'''

PRODUCT_DETAIL_TEMPLATE = '''
<!doctype html>
<title>{{ product.name }}</title>
<h1>{{ product.name }}</h1>
<p>{{ product.description }}</p>
<h2>Reviews</h2>
<ul>
  {% for review in reviews %}
    <li>
      <strong>Rating: {{ review.rating }}</strong><br>
      {{ review.review_text }}<br>
      <em>Posted at {{ review.created_at }}</em>
    </li>
  {% else %}
    <li>No reviews yet.</li>
  {% endfor %}
</ul>
<a href="{{ url_for('add_review', product_id=product.id) }}">Add Review</a>
<br>
<a href="{{ url_for('index') }}">Back to Products</a>
'''

ADD_REVIEW_TEMPLATE = '''
<!doctype html>
<title>Add Review</title>
<h1>Add Review for {{ product.name }}</h1>
<form method="post">
    <!-- CSRF protection -->
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <label for="review_text">Review:</label><br>
    <textarea id="review_text" name="review_text" rows="4" cols="50"></textarea><br>
    <label for="rating">Rating (1-5):</label><br>
    <input type="number" id="rating" name="rating" min="1" max="5" required><br><br>
    <input type="submit" value="Submit">
</form>
<a href="{{ url_for('product_detail', product_id=product.id) }}">Back to Product</a>
'''

@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template_string(INDEX_TEMPLATE, products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ? ORDER BY created_at DESC', (product_id,)).fetchall()
    conn.close()
    if product is None:
        return 'Product not found', 404
    return render_template_string(PRODUCT_DETAIL_TEMPLATE, product=product, reviews=reviews)

@app.route('/product/<int:product_id>/review', methods=['GET', 'POST'])
def add_review(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        conn.close()
        return 'Product not found', 404

    if request.method == 'POST':
        # --- CSRF Protection ---
        session_token = session.get('csrf_token')
        form_token = request.form.get('csrf_token')
        if not session_token or not form_token or session_token != form_token:
            conn.close()
            return "CSRF token mismatch", 400
        
        # --- Retrieve and validate input ---
        review_text = request.form.get('review_text', '')
        try:
            rating = int(request.form.get('rating', ''))
        except ValueError:
            conn.close()
            return "Invalid rating", 400

        if rating < 1 or rating > 5:
            conn.close()
            return "Rating must be between 1 and 5", 400

        # --- Insert the review securely ---
        # Using parameterized queries prevents SQL injection.
        user_id = session.get('user_id')
        conn.execute('INSERT INTO reviews (product_id, user_id, review_text, rating) VALUES (?, ?, ?, ?)', 
                     (product_id, user_id, review_text, rating))
        conn.commit()
        conn.close()
        return redirect(url_for('product_detail', product_id=product_id))
    else:
        csrf_token = generate_csrf_token()
        conn.close()
        return render_template_string(ADD_REVIEW_TEMPLATE, product=product, csrf_token=csrf_token)

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
