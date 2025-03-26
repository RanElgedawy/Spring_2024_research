# secure_reviews.py
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from wtforms import Form, StringField, IntegerField, validators
import bleach

app = Flask(__name__)
app.config.update(
    SECRET_KEY='your-secret-key-here',  # Change this in production!
    SQLALCHEMY_DATABASE_URI='sqlite:///reviews.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    WTF_CSRF_TIME_LIMIT=3600
)

# Initialize extensions
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Database models
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Assuming users exist in another table
    product_id = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Form class with validation
class ReviewForm(Form):
    review_text = StringField('Review', [
        validators.Length(min=10, max=2000),
        validators.InputRequired()
    ])
    rating = IntegerField('Rating', [
        validators.NumberRange(min=1, max=5),
        validators.InputRequired()
    ])

# Create tables (in-memory for testing)
@app.before_first_request
def initialize_database():
    db.create_all()

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    return bleach.clean(text, tags=allowed_tags, strip=True)

@app.route('/submit-review/<int:product_id>', methods=['GET', 'POST'])
def submit_review(product_id):
    # In a real app, get user_id from session/auth system
    # For demo purposes, we'll hardcode a user ID
    user_id = session.get('user_id', 1)  # Replace with actual auth system
    
    form = ReviewForm(request.form)
    
    if request.method == 'POST' and form.validate():
        # Sanitize and validate input
        clean_text = sanitize_input(form.review_text.data)
        
        try:
            review = Review(
                user_id=user_id,
                product_id=product_id,
                review_text=clean_text,
                rating=form.rating.data
            )
            db.session.add(review)
            db.session.commit()
            return redirect(url_for('thank_you'))
        except Exception as e:
            db.session.rollback()
            return "Error saving review", 500
    
    return render_template('review_form.html', form=form, product_id=product_id)

@app.route('/thank-you')
def thank_you():
    return "Thank you for your review!"

# Test route to display reviews
@app.route('/product/<int:product_id>')
def product_details(product_id):
    reviews = Review.query.filter_by(product_id=product_id).all()
    return render_template('product.html', reviews=reviews)

if __name__ == '__main__':
    app.run(debug=True)