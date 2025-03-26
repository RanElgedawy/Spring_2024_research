from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange
import sqlite3
from flask_wtf.csrf import CSRFProtect

# Initialize Flask app and CSRF protection
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # You should change this to a random secret key for production
csrf = CSRFProtect(app)

# Database setup
DATABASE = 'ecommerce.db'

# Helper function to execute SQL commands
def execute_db(query, args=()):
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute(query, args)
        con.commit()
    return cur

# Create reviews table if it doesn't exist
def init_db():
    execute_db("DROP TABLE IF EXISTS reviews")
    query = '''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
        review TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    '''
    execute_db(query)

# Flask-WTF form for review submission
class ReviewForm(FlaskForm):
    review = TextAreaField('Review', validators=[DataRequired()])
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Submit Review')

# Route to submit a review
@app.route('/submit_review/<int:product_id>', methods=['GET', 'POST'])
def submit_review(product_id):
    form = ReviewForm()

    if form.validate_on_submit():
        user_id = 1  # Placeholder for user_id; assume user is logged in with ID 1
        review_text = form.review.data
        rating = form.rating.data

        # SQL injection protection using parameterized queries
        query = '''
        INSERT INTO reviews (user_id, product_id, rating, review)
        VALUES (?, ?, ?, ?)
        '''
        execute_db(query, (user_id, product_id, rating, review_text))
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('submit_review', product_id=product_id))

    return render_template('submit_review.html', form=form, product_id=product_id)

# Route to display reviews for a product
@app.route('/product/<int:product_id>/reviews')
def product_reviews(product_id):
    query = '''
    SELECT user_id, rating, review, created_at
    FROM reviews
    WHERE product_id = ?
    '''
    reviews = execute_db(query, (product_id,)).fetchall()
    return render_template('product_reviews.html', reviews=reviews, product_id=product_id)

if __name__ == '__main__':
    init_db()  # Initialize the database and create tables if they don't exist
    app.run(debug=True)