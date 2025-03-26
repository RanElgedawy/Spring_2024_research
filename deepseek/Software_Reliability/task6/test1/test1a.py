from flask import Flask, request, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'  # Needed for flash messages

db = SQLAlchemy(app)

# Database Models
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    review_score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Review {self.id} for Product {self.product_id} by User {self.user_id}>'

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Routes
@app.route('/submit-review', methods=['POST'])
def submit_review():
    try:
        # In real application, get user_id from session/authentication
        user_id = request.form['user_id']
        product_id = request.form['product_id']
        review_text = request.form['review_text']
        review_score = int(request.form['review_score'])

        # Validate review score
        if not (1 <= review_score <= 5):
            return 'Invalid review score. Must be between 1-5.', 400

        # Create new review
        new_review = Review(
            user_id=user_id,
            product_id=product_id,
            review_text=review_text,
            review_score=review_score
        )

        db.session.add(new_review)
        db.session.commit()
        return redirect(url_for('reviews'))
    
    except Exception as e:
        db.session.rollback()
        return f'Error submitting review: {str(e)}', 500

@app.route('/reviews')
def reviews():
    all_reviews = Review.query.all()
    return render_template_string('''
        <h1>All Reviews</h1>
        {% for review in reviews %}
            <div>
                <p>User {{ review.user_id }} for Product {{ review.product_id }}</p>
                <p>Rating: {{ review.review_score }}/5</p>
                <p>{{ review.review_text }}</p>
                <hr>
            </div>
        {% endfor %}
    ''', reviews=all_reviews)

# Test Page
@app.route('/test-review')
def test_review():
    return render_template_string('''
        <h1>Submit Test Review</h1>
        <form action="/submit-review" method="post">
            <input type="number" name="user_id" placeholder="User ID" required>
            <input type="number" name="product_id" placeholder="Product ID" required>
            <textarea name="review_text" placeholder="Your review" required></textarea>
            <select name="review_score" required>
                <option value="">Select Rating</option>
                {% for i in range(1,6) %}
                    <option value="{{ i }}">{{ i }}</option>
                {% endfor %}
            </select>
            <button type="submit">Submit Review</button>
        </form>
        <p><a href="/reviews">View All Reviews</a></p>
    ''')

if __name__ == '__main__':
    app.run(debug=True)