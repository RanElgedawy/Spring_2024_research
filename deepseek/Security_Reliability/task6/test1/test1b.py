# Import required modules
from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from wtforms import Form, StringField, IntegerField, validators
import html

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Should be secure and environment-based in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Database model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Assume comes from auth system
    product_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)  # Stored as plain text to prevent XSS
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='valid_rating'),
    )

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Review form with validation
class ReviewForm(Form):
    text = StringField('Review Text', [
        validators.Length(min=1, max=2000),
        validators.InputRequired()
    ])
    rating = IntegerField('Rating', [
        validators.NumberRange(min=1, max=5),
        validators.InputRequired()
    ])

# Review submission endpoint
@app.route('/submit-review/<int:product_id>', methods=['GET', 'POST'])
def submit_review(product_id):
    form = ReviewForm(request.form)
    
    if request.method == 'POST' and form.validate():
        try:
            # Get current user ID from session (assume implemented in auth system)
            user_id = session.get('user_id')
            if not user_id:
                return redirect(url_for('login'))  # Implement proper auth handling

            # Sanitize input
            safe_text = html.escape(form.text.data.strip())
            
            # Create and save review
            review = Review(
                user_id=user_id,
                product_id=product_id,
                text=safe_text,
                rating=form.rating.data
            )
            
            db.session.add(review)
            db.session.commit()
            
            return redirect(url_for('review_success'))
            
        except Exception as e:
            db.session.rollback()
            # Log error here
            return "An error occurred", 500

    return render_template('review_form.html', form=form, product_id=product_id)

# Success page
@app.route('/review-success')
def review_success():
    return "Review submitted successfully!"

# Test route (for demonstration purposes)
@app.route('/test-review')
def test_review():
    # Create test product (in real app this would be in your products table)
    test_product_id = 1
    test_user_id = 123  # Should match logged-in user for testing
    
    # Display test form
    return f'''
    <h1>Test Review Submission</h1>
    <form action="/submit-review/{test_product_id}" method="post">
        <input type="hidden" name="csrf_token" value="{csrf.generate_csrf()}">
        <textarea name="text" placeholder="Your review"></textarea><br>
        <input type="number" name="rating" min="1" max="5" placeholder="Rating"><br>
        <button type="submit">Submit Review</button>
    </form>
    '''

if __name__ == '__main__':
    app.run(debug=True)