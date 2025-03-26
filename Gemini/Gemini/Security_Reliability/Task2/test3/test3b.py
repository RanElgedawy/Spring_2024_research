from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'  # Replace with your database URI

db = SQLAlchemy(app)

# Model definitions
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, nullable=False)

# API endpoints
@app.route('/products/<int:product_id>')
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.serialize())
    return jsonify({'error': 'Product not found'}), 404

@app.route('/cart', methods=['POST'])
def add_to_cart():
    # Authenticate user using JWT
    auth_token = request.headers.get('Authorization')
    if not auth_token:
        return jsonify({'error': 'Authentication required'}), 401
    try:
        payload = jwt.decode(auth_token, app.config['SECRET_KEY'])
        user_id = payload['user_id']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

    product_id = request.json.get('product_id')
    product = Product.query.get(product_id)
    if not product or product.quantity == 0:
        return jsonify({'error': 'Product is out of stock'}), 400

    # Check if item already in cart
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(cart_item)

    db.session.commit()
    return jsonify({'message': 'Item added to cart'})

# ... other API endpoints for authentication, retrieving cart items, etc.

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    app.run(debug=True)