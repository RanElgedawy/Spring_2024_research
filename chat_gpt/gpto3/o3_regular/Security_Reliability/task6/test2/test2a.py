from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, HiddenField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
# Use a strong secret key in production!
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database model for reviews.
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)

# WTForms form for review submission.
class ReviewForm(FlaskForm):
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    text = TextAreaField('Review', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Submit Review')

# Automatically create the database tables on the first request.
@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()

# Simulate a logged-in user by setting a user ID.
@app.before_request
def simulate_login():
    session['user_id'] = 1

# Route to display and process the review form.
@app.route('/review/<int:product_id>', methods=['GET', 'POST'])
def review(product_id):
    form = ReviewForm(product_id=product_id)
    if form.validate_on_submit():
        # SQLAlchemy's parameterized queries prevent SQL injection.
        new_review = Review(
            user_id=session.get('user_id'),
            product_id=product_id,
            rating=form.rating.data,
            text=form.text.data
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('review', product_id=product_id))
    return render_template('review.html', form=form, product_id=product_id)

# Route to view reviews for a specific product.
@app.route('/reviews/<int:product_id>')
def reviews(product_id):
    # Jinja2 autoescaping makes output safe from XSS.
    reviews = Review.query.filter_by(product_id=product_id).all()
    return render_template('reviews.html', reviews=reviews, product_id=product_id)

if __name__ == '__main__':
    app.run(debug=True)
