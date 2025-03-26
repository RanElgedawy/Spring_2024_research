from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Purchase model (assuming this exists in the database)
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)

# Review model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text)
    review_score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='unique_user_product_review'),
    )

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Helper function to check purchases
def has_purchased(user_id, product_id):
    return Purchase.query.filter_by(
        user_id=user_id,
        product_id=product_id
    ).first() is not None

# Review submission endpoint
@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.get_json()
    
    # Validate input
    if not all(key in data for key in ['user_id', 'product_id', 'review_text', 'review_score']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        user_id = int(data['user_id'])
        product_id = int(data['product_id'])
        review_score = int(data['review_score'])
    except ValueError:
        return jsonify({'error': 'Invalid ID or score format'}), 400
    
    if not (1 <= review_score <= 5):
        return jsonify({'error': 'Score must be between 1-5'}), 400
    
    if not has_purchased(user_id, product_id):
        return jsonify({'error': 'User has not purchased this product'}), 403
    
    # Check for existing review
    existing_review = Review.query.filter_by(
        user_id=user_id,
        product_id=product_id
    ).first()
    
    if existing_review:
        return jsonify({'error': 'User already reviewed this product'}), 409
    
    # Create new review
    new_review = Review(
        user_id=user_id,
        product_id=product_id,
        review_text=data['review_text'],
        review_score=review_score
    )
    
    try:
        db.session.add(new_review)
        db.session.commit()
        return jsonify({'message': 'Review submitted successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Test endpoint to get product reviews
@app.route('/product_reviews/<int:product_id>', methods=['GET'])
def get_product_reviews(product_id):
    reviews = Review.query.filter_by(product_id=product_id).all()
    return jsonify([{
        'user_id': r.user_id,
        'review_text': r.review_text,
        'review_score': r.review_score,
        'timestamp': r.timestamp.isoformat()
    } for r in reviews])

# Test endpoint to add purchase (for testing purposes)
@app.route('/test/add_purchase', methods=['POST'])
def add_test_purchase():
    data = request.get_json()
    try:
        new_purchase = Purchase(
            user_id=int(data['user_id']),
            product_id=int(data['product_id'])
        )
        db.session.add(new_purchase)
        db.session.commit()
        return jsonify({'message': 'Purchase recorded'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)