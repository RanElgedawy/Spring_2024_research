# Import Flask and other necessary modules
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import validates
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define database models

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    # Add more user-related fields as needed

# Define the Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Add more product-related fields as needed

# Define the Purchase model
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, ForeignKey('product.id'), nullable=False)
    # Add more purchase-related fields as needed
    user = relationship("User", backref="purchases")
    product = relationship("Product", backref="purchases")

# Define the Review model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=False)

    @validates('rating')
    def validate_rating(self, key, rating):
        assert 1 <= rating <= 5, "Rating must be between 1 and 5."
        return rating

# Drop existing tables and create new ones
db.drop_all()
db.create_all()

# Insert test values into the tables
test_user = User(username="test_user")
db.session.add(test_user)

test_product = Product(name="Test Product")
db.session.add(test_product)

test_purchase = Purchase(user=test_user, product=test_product)
db.session.add(test_purchase)

db.session.commit()

# Routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_review', methods=['POST'])
def submit_review():
    product_id = request.form['product_id']
    user_id = request.form['user_id']
    rating = int(request.form['rating'])  # Convert rating to an integer
    review_text = request.form['review_text']

    if not rating or not review_text:
        return "Error: Both rating and review text must be provided."

    # Check if the user has purchased the product
    try:
        with app.app_context():
            purchase = Purchase.query.filter_by(user_id=user_id, product_id=product_id).one()
    except NoResultFound:
        return "Error: User has not purchased this product."
    except MultipleResultsFound:
        return "Error: Multiple purchases found for this user and product."

    # Save the review
    try:
        with app.app_context():
            review = Review(product_id=product_id, user_id=user_id, rating=rating, review_text=review_text)
            db.session.add(review)
            db.session.commit()
        return redirect(url_for('index'))
    except IntegrityError:
        return "Error: Review submission failed due to integrity error."

@app.route('/view_reviews/<int:product_id>')
def view_reviews(product_id):
    try:
        with app.app_context():
            reviews = Review.query.filter_by(product_id=product_id).all()
        return render_template('view_reviews.html', reviews=reviews)
    except NoResultFound:
        return "No reviews found for this product."

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)