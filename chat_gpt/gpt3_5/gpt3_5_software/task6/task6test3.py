from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Add other user attributes as needed

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Add other product attributes as needed

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    text_review = db.Column(db.String(255)) 
    review_score = db.Column(db.Integer)

    def __init__(self, user_id, product_id, text_review, review_score):
        self.user_id = user_id
        self.product_id = product_id
        self.text_review = text_review
        self.review_score = review_score

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

    def __init__(self, user_id, product_id):
        self.user_id = user_id
        self.product_id = product_id

@app.route('/add_review', methods=['POST'])
def add_review():
  with app.app_context():  
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    text_review = request.json.get('text_review')
    review_score = request.json.get('review_score')

    if not all([user_id, product_id, text_review, review_score]):
        return jsonify({'error': 'All fields are required: user_id, product_id, text_review, review_score'}), 400

    if not text_review.strip():  # Check if text_review is empty or only contains whitespace
        return jsonify({'error': 'text_review cannot be empty'}), 400

    if not isinstance(review_score, int) or review_score < 1 or review_score > 5:
        return jsonify({'error': 'Review score must be an integer between 1 and 5'}), 400

    user = User.query.get(user_id)
    if user is None:
        return jsonify({'error': 'User does not exist'}), 404

    product = Product.query.get(product_id)
    if product is None:
        return jsonify({'error': 'Product does not exist'}), 404

    # Check if the user has purchased the product
    if not has_purchased(user_id, product_id):
        return jsonify({'error': 'User has not purchased this product'}), 400

    new_review = Review(user_id=user_id, product_id=product_id, text_review=text_review, review_score=review_score)
    db.session.add(new_review)
    db.session.commit()

    return jsonify({'message': 'Review added successfully'}), 201

def has_purchased(user_id, product_id):
    # Check if the user has purchased the product
    return Purchase.query.filter_by(user_id=user_id, product_id=product_id).first() is not None

if __name__ == '__main__':
   with app.app_context(): 
    db.create_all()
    db.session.add(Product())
    db.session.add(User())
    db.session.add(Purchase(user_id = 1, product_id = 1))
    db.session.commit()
    app.run(debug=True)