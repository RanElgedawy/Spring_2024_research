from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length
from flask_sqlalchemy import SQLAlchemy
from wtforms.csrf.session import SessionCSRF
import os
import sqlite3
from flask_wtf.csrf import CSRFProtect

# Flask setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
csrf = CSRFProtect(app)

# Database setup
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

# Purchase model to track purchases
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

# Review model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)

# Form class with CSRF protection
class ReviewForm(FlaskForm):
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    text = TextAreaField('Review Text', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Submit')

# Home route to list reviews
@app.route('/')
def index():
    reviews = Review.query.all()
    return render_template('index.html', reviews=reviews)

# Route to add a review
@app.route('/add_review/<int:product_id>', methods=['GET', 'POST'])
def add_review(product_id):
    form = ReviewForm()
    user_id = 1  # Assume a logged-in user with ID 1

    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        flash('User does not exist.', 'error')
        return redirect(url_for('index'))

    # Check if the user has purchased the product
    purchase = Purchase.query.filter_by(user_id=user_id, product_id=product_id).first()
    if not purchase:
        flash('You can only review products you have purchased.', 'error')
        return redirect(url_for('index'))

    if form.validate_on_submit():
        # Save the review
        new_review = Review(
            product_id=product_id,
            user_id=user_id,
            rating=form.rating.data,
            text=form.text.data
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Review added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_review.html', form=form)

# Create the database and some initial data
with app.app_context():
    db.drop_all()
    db.create_all()

    # Add some test data (uncomment this block on the first run)
    if not User.query.first():
        user1 = User(username='john_doe')
        user2 = User(username='jane_doe')
        product1 = Product(name='Product 1')
        product2 = Product(name='Product 2')
        db.session.add_all([user1, user2, product1, product2])
        db.session.commit()

        purchase1 = Purchase(user_id=user1.id, product_id=product1.id)
        purchase2 = Purchase(user_id=user2.id, product_id=product2.id)
        db.session.add_all([purchase1, purchase2])
        db.session.commit()

# Main block to run the app
if __name__ == '__main__':
    app.run(debug=True)