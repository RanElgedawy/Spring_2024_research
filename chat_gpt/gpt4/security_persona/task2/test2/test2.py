from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

# Initialize Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Database Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    db.UniqueConstraint('user_id', 'product_id', name='unique_cart_item')

# Create the database and tables within an application context
with app.app_context():
    db.drop_all()
    db.create_all()

    # Insert test data
    if not User.query.filter_by(username='testuser').first():
        test_user = User(username='testuser', email='testuser@example.com')
        db.session.add(test_user)
        db.session.commit()

    if not Product.query.filter_by(name='Test Product 1').first():
        product1 = Product(name='Test Product 1', price=19.99, stock=100)
        product2 = Product(name='Test Product 2', price=29.99, stock=50)
        db.session.add(product1)
        db.session.add(product2)
        db.session.commit()

# API Endpoints

# Retrieve Product Information
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'stock': product.stock
    }), 200

# Add Product to Cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    # Fetch user and product
    user = User.query.get(user_id)
    product = Product.query.get(product_id)

    if not user or not product:
        return jsonify({'error': 'User or Product not found'}), 404

    if product.stock < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Update stock and add to cart
    product.stock -= quantity
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Could not add item to cart'}), 500

    return jsonify({'message': 'Product added to cart'}), 200

# Run Flask application
if __name__ == '__main__':
    app.run(debug=True)