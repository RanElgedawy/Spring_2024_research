from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
db = SQLAlchemy(app)

# Define the database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    text = db.Column(db.Text)
    score = db.Column(db.Integer)

    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    product = db.relationship('Product', backref=db.backref('reviews', lazy=True))

# Create database tables
with app.app_context():
    # Add a product and user for testing purposes
    # db.session.add(Product(name = "test"))
    # db.session.add(User(username = "user"))
    db.session.add(Purchase(user_id = 1, product_id = 1))
    db.session.commit()
    db.create_all()

# Function to check if a user has purchased a product
def has_user_purchased_product(user_id, product_id):
    return Purchase.query.filter_by(user_id=user_id, product_id=product_id).first() is not None

# Route to add a review
@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = request.form['user_id']
    product_id = request.form['product_id']
    text = request.form['text']
    score = request.form['score']

    # Check if the text review, score, and user ID are provided
    if not text or not score or not user_id or not product_id:
        return jsonify({'error': 'Text review, score, user ID, and product ID are required'}), 400

    # Check if the product exists
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product does not exist'}), 400

    # Check if the review score is between 1 and 5 (inclusive)
    try:
        score = int(score)
        if score < 1 or score > 5:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'Review score must be an integer between 1 and 5'}), 400

    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        user = User(id=user_id, username=f'user_{user_id}')
        db.session.add(user)

    # Check if the user has purchased the product
    if not has_user_purchased_product(user_id, product_id):
        return jsonify({'error': 'User has not purchased the product'}), 400

    review = Review(user_id=user_id, product_id=product_id, text=text, score=score)
    db.session.add(review)
    db.session.commit()

    return jsonify({'message': 'Review added successfully'}), 200

# Route to test the functionality
@app.route('/')
def index():
    # Assuming user is logged in and their user_id is available
    user_id = 1
    # Assuming product_id of the purchased product is available
    product_id = 1
    return render_template('index.html', user_id=user_id, product_id=product_id)

if __name__ == '__main__':
    app.run(debug=True)