from flask import Flask, request, render_template_string, g, redirect, url_for, flash
import sqlite3
import random
import string
from markupsafe import escape

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))  # For CSRF protection and sessions

DATABASE = 'reviews.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# CSRF protection token generator
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

# Initialize the database schema
def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

# Create a review route
@app.route('/review/<int:product_id>', methods=['GET', 'POST'])
def review(product_id):
    db = get_db()

    # Fetch the product to make sure it exists
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        return 'Product not found!', 404

    if request.method == 'POST':
        # Validate CSRF token
        if request.form.get('_csrf_token') != session.get('_csrf_token'):
            return 'CSRF validation failed!', 403
        
        review_text = request.form['review']
        rating = request.form['rating']

        # Validate the rating
        if not rating.isdigit() or not (1 <= int(rating) <= 5):
            flash('Rating must be a number between 1 and 5.')
            return redirect(url_for('review', product_id=product_id))

        # Escape and sanitize review text
        safe_review_text = escape(review_text)

        # Insert review into database (with parameterized query to prevent SQL Injection)
        db.execute('INSERT INTO reviews (product_id, review_text, rating) VALUES (?, ?, ?)', 
                   (product_id, safe_review_text, int(rating)))
        db.commit()

        flash('Review submitted successfully!')
        return redirect(url_for('review', product_id=product_id))

    return render_template_string('''
        <h2>Leave a Review for {{ product['name'] }}</h2>
        <form method="POST">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
            <label for="review">Review:</label><br>
            <textarea name="review" required></textarea><br>
            <label for="rating">Rating (1-5):</label><br>
            <input type="number" name="rating" min="1" max="5" required><br><br>
            <input type="submit" value="Submit">
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
    ''', product=product)

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)