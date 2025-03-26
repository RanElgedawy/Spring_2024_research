from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Initialize the Flask app and the database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    # Ensure that the rating is between 1 and 5
    def __init__(self, user_id, product_id, review_text, rating):
        self.user_id = user_id
        self.product_id = product_id
        self.review_text = review_text
        self.rating = max(1, min(5, rating))

# Create the tables in the database
with app.app_context():
    db.drop_all()
    db.create_all()

# Sample route to add a review for a product
@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    review_text = request.json.get('review_text')
    rating = request.json.get('rating')

    # Check if the user has purchased the product
    purchase = Purchase.query.filter_by(user_id=user_id, product_id=product_id).first()
    if not purchase:
        return jsonify({'error': 'User has not purchased this product.'}), 400

    # Add the review to the database
    review = Review(user_id=user_id, product_id=product_id, review_text=review_text, rating=rating)
    db.session.add(review)
    db.session.commit()

    return jsonify({'message': 'Review added successfully!'})

# Route to get all reviews for a product
@app.route('/reviews/<int:product_id>', methods=['GET'])
def get_reviews(product_id):
    reviews = Review.query.filter_by(product_id=product_id).all()
    reviews_list = [{'user_id': r.user_id, 'review_text': r.review_text, 'rating': r.rating} for r in reviews]
    return jsonify(reviews_list)

# Sample data creation for testing
def create_sample_data():
    user1 = User(username='user1')
    user2 = User(username='user2')
    product1 = Product(name='Product 1')
    product2 = Product(name='Product 2')

    db.session.add_all([user1, user2, product1, product2])
    db.session.commit()

    purchase1 = Purchase(user_id=user1.id, product_id=product1.id)
    purchase2 = Purchase(user_id=user2.id, product_id=product2.id)

    db.session.add_all([purchase1, purchase2])
    db.session.commit()

# Run this only if the database is empty
with app.app_context():
    if not User.query.first():
        create_sample_data()

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)