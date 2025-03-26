from flask import Flask, request, render_template, redirect, url_for, session, g
from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField
from wtforms.validators import DataRequired, NumberRange
import sqlite3
import os
from wtforms.csrf.session import SessionCSRF
import re

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Secret key for CSRF protection

DATABASE = 'reviews.db'

# Initialize the database
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

def init_db():
    db = get_db()
    db.execute("DROP TABLE IF EXISTS reviews")
    db.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            rating INTEGER NOT NULL
        )
    ''')
    db.commit()

# CSRF form class
class ReviewForm(FlaskForm):
    review_text = TextAreaField('Review', validators=[DataRequired()])
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])

# Helper: Strip dangerous HTML tags for XSS prevention
def sanitize_input(text):
    clean_text = re.sub(r'<[^>]*?>', '', text)  # Remove HTML tags
    return clean_text

# Route to handle review submission
@app.route('/submit_review/<int:product_id>', methods=['GET', 'POST'])
def submit_review(product_id):
    if 'user_id' not in session:  # Simulate user logged in via session
        return redirect(url_for('login'))

    form = ReviewForm()
    if form.validate_on_submit():
        user_id = session['user_id']  # Retrieve logged-in user ID
        review_text = sanitize_input(form.review_text.data)
        rating = form.rating.data

        # Secure parameterized query to prevent SQL injection
        db = get_db()
        db.execute('''
            INSERT INTO reviews (user_id, product_id, review_text, rating) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, review_text, rating))
        db.commit()

        return redirect(url_for('success'))

    return render_template('review_form.html', form=form, product_id=product_id)

# Success page after review submission
@app.route('/success')
def success():
    return "Review submitted successfully!"

# Login page simulation (for testing)
@app.route('/login')
def login():
    session['user_id'] = 1  # Simulate user logged in with user_id 1
    return redirect(url_for('submit_review', product_id=1))

# Initialize the database before the first request
@app.before_first_request
def initialize():
    init_db()

# Main route for testing
@app.route('/')
def index():
    return redirect(url_for('login'))  # Redirect to login

# Test environment to run Flask app
if __name__ == '__main__':
    app.run(debug=True)