from flask import Flask, request, session, redirect, url_for, g, abort
from flask import render_template_string
import sqlite3
import os
import html

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management
DATABASE = 'reviews.db'

# Database setup
def init_db():
    with app.app_context():
        db = get_db()
        db.execute("DROP TABLE IF EXISTS products")
        db.execute("DROP TABLE IF EXISTS reviews")

        db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                review_text TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )''')
        # Insert test product if none exists
        if not db.execute('SELECT 1 FROM products LIMIT 1').fetchone():
            db.execute('INSERT INTO products (name) VALUES (?)', ('Test Product',))
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# CSRF Protection Middleware
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = os.urandom(24).hex()
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

def validate_csrf_token():
    token = session.pop('_csrf_token', None)
    if not token or token != request.form.get('csrf_token'):
        abort(403)

# Routes
@app.route('/submit_review/<int:product_id>', methods=['GET', 'POST'])
def submit_review(product_id):
    # In real implementation, get user_id from session/auth system
    # For demo purposes, we'll hardcode user_id to 1
    user_id = 1  
    
    if request.method == 'POST':
        validate_csrf_token()
        
        # Validate product exists
        db = get_db()
        product = db.execute(
            'SELECT 1 FROM products WHERE id = ?', 
            (product_id,)
        ).fetchone()
        if not product:
            abort(404)
        
        # Get and validate input
        review_text = request.form.get('review_text', '').strip()
        try:
            rating = int(request.form.get('rating', 0))
        except ValueError:
            rating = 0
            
        errors = []
        if not review_text:
            errors.append('Review text is required')
        if rating < 1 or rating > 5:
            errors.append('Rating must be between 1-5')
            
        if not errors:
            # Sanitize input and insert into database
            db.execute('''
                INSERT INTO reviews 
                (product_id, user_id, review_text, rating)
                VALUES (?, ?, ?, ?)
            ''', (product_id, user_id, review_text, rating))
            db.commit()
            return redirect(url_for('review_submitted'))
        
        return render_template_string(TEMPLATE, 
            product_id=product_id,
            errors=errors,
            review_text=review_text,
            rating=rating)
    
    return render_template_string(TEMPLATE, product_id=product_id)

@app.route('/review_submitted')
def review_submitted():
    return 'Review submitted successfully!'

# HTML Template with automatic output escaping
TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Submit Review</title>
</head>
<body>
    <h1>Submit Review for Product {{ product_id }}</h1>
    {% if errors %}
        <ul style="color: red">
            {% for error in errors %}
                <li>{{ error }}</li>
            {% endfor %}
        </ul>
    {% endif %}
    <form method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        
        <label for="review_text">Review:</label><br>
        <textarea name="review_text" id="review_text" rows="4" cols="50" required>{{ review_text|default('', true) }}</textarea><br>
        
        <label for="rating">Rating (1-5):</label>
        <input type="number" name="rating" id="rating" min="1" max="5" required value="{{ rating|default('', true) }}"><br>
        
        <button type="submit">Submit Review</button>
    </form>
</body>
</html>
'''

if __name__ == '__main__':
    init_db()
    app.run(debug=True)