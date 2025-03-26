from flask import Flask, request, render_template_string, redirect, url_for, flash, session
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange
import sqlite3
import os

app = Flask(__name__)
# Set a strong secret key for session and CSRF protection
app.config['SECRET_KEY'] = 'this-should-be-a-secure-random-value'
csrf = CSRFProtect(app)

DATABASE = 'reviews.db'

# --- Database initialization ---
def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    # Create products table (if it doesn't exist) for demonstration.
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("DROP TABLE IF EXISTS reviews")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    # Create reviews table.
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            review_text TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    # Insert a sample product if table is empty
    cur.execute('SELECT COUNT(*) FROM products')
    if cur.fetchone()[0] == 0:
        cur.execute('INSERT INTO products (name) VALUES (?)', ('Sample Product',))
    conn.commit()
    conn.close()

init_db()

# --- WTForms form definition ---
class ReviewForm(FlaskForm):
    review_text = TextAreaField('Review', validators=[DataRequired()])
    rating = SelectField('Rating', choices=[('1','1'), ('2','2'), ('3','3'), ('4','4'), ('5','5')],
                         validators=[DataRequired()])
    submit = SubmitField('Submit Review')

# --- Helper function to get DB connection ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- Routes ---
@app.before_request
def simulate_login():
    # Simulate a logged in user by setting a fixed user_id.
    session['user_id'] = 42

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_review(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        conn.close()
        return "Product not found", 404

    form = ReviewForm()
    if form.validate_on_submit():
        # Get form data and use parameterized queries to prevent SQL injection.
        review_text = form.review_text.data
        rating = int(form.rating.data)
        user_id = session.get('user_id')
        conn.execute('INSERT INTO reviews (product_id, user_id, rating, review_text) VALUES (?, ?, ?, ?)',
                     (product_id, user_id, rating, review_text))
        conn.commit()
        conn.close()
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('product_review', product_id=product_id))
    
    # Retrieve reviews to display (Flask autoescaping in templates helps prevent XSS)
    reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    template = '''
    <!doctype html>
    <html lang="en">
    <head>
        <title>{{ product['name'] }} - Reviews</title>
    </head>
    <body>
        <h1>{{ product['name'] }}</h1>
        <h2>Submit a Review</h2>
        <form method="post">
            {{ form.hidden_tag() }}
            <p>
                {{ form.review_text.label }}<br>
                {{ form.review_text(cols=40, rows=5) }}
            </p>
            <p>
                {{ form.rating.label }}<br>
                {{ form.rating() }}
            </p>
            <p>{{ form.submit() }}</p>
        </form>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <ul>
                {% for category, message in messages %}
                    <li style="color: green;">{{ message }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}
        <h2>Existing Reviews</h2>
        {% for review in reviews %}
            <div style="border:1px solid #ccc; padding: 10px; margin-bottom:10px;">
                <strong>Rating:</strong> {{ review['rating'] }}<br>
                <strong>Review:</strong> {{ review['review_text'] }}
            </div>
        {% else %}
            <p>No reviews yet. Be the first to review!</p>
        {% endfor %}
    </body>
    </html>
    '''
    return render_template_string(template, form=form, product=product, reviews=reviews)

if __name__ == '__main__':
    # Only for development: set debug=True for live reload and better error messages.
    app.run(debug=True)
