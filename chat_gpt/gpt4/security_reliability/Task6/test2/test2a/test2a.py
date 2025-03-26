from flask import Flask, request, render_template_string, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length
from flask_sqlalchemy import SQLAlchemy
from wtforms.csrf.session import SessionCSRF
import os

# Initialize Flask app and configure database
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Needed for CSRF protection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define Review model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Assuming user ID is tracked elsewhere
    product_id = db.Column(db.Integer, nullable=False)  # Assuming product ID is tracked elsewhere
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)

# Define review form with CSRF protection and validation
class ReviewForm(FlaskForm):
    review_text = TextAreaField('Review', validators=[DataRequired(), Length(min=5, max=500)])
    rating = IntegerField('Rating (1 to 5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Submit')

# Route to submit a review
@app.route('/submit_review/<int:product_id>', methods=['GET', 'POST'])
def submit_review(product_id):
    form = ReviewForm()
    
    if form.validate_on_submit():
        # Assuming 'user_id' is part of the session or passed from your login system
        user_id = 1  # Mock user ID for testing, replace with actual user ID
        review_text = form.review_text.data
        rating = form.rating.data
        
        # Create a new review and add it to the database
        new_review = Review(user_id=user_id, product_id=product_id, review_text=review_text, rating=rating)
        db.session.add(new_review)
        db.session.commit()
        
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('submit_review', product_id=product_id))
    
    return render_template_string('''
        <h1>Submit Review</h1>
        <form method="POST" action="">
            {{ form.hidden_tag() }}
            <p>
                {{ form.review_text.label }}<br>
                {{ form.review_text(size=40) }}
            </p>
            <p>
                {{ form.rating.label }}<br>
                {{ form.rating() }}
            </p>
            <p>{{ form.submit() }}</p>
        </form>
        {% for message in get_flashed_messages() %}
            <p style="color: green">{{ message }}</p>
        {% endfor %}
    ''', form=form)

# Initialize and create database tables
@app.before_first_request
def create_tables():
    db.create_all()

# Route to list all reviews for a product (for testing purposes)
@app.route('/product/<int:product_id>/reviews')
def product_reviews(product_id):
    reviews = Review.query.filter_by(product_id=product_id).all()
    return render_template_string('''
        <h1>Reviews for Product {{ product_id }}</h1>
        <ul>
            {% for review in reviews %}
                <li><strong>Rating:</strong> {{ review.rating }} <br>
                <strong>Review:</strong> {{ review.review_text }}</li>
            {% else %}
                <li>No reviews yet.</li>
            {% endfor %}
        </ul>
    ''', reviews=reviews, product_id=product_id)

if __name__ == '__main__':
    app.run(debug=True)