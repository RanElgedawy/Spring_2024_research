from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'  # Change to MySQL if needed
app.config['JWT_SECRET_KEY'] = 'supersecretkey'  # Use a more secure key for production

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Models: User, Product, CartItem
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # Assume this is hashed

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)  # Quantity of items in stock

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product', backref='cart_items')

# Create tables if they don't exist
@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()

# Helper function to validate stock availability
def check_product_stock(product_id, quantity):
    product = Product.query.filter_by(id=product_id).first()
    if product and product.stock >= quantity:
        return True, product
    return False, None

# API Endpoints

# Register a new user (simplified, no password hashing here for demo purposes)
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    try:
        db.session.commit()
        return jsonify(message="User registered successfully"), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify(message="Username already exists"), 409

# Login to get JWT token
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if user:
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    return jsonify(message="Invalid credentials"), 401

# Retrieve product info by product ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.filter_by(id=product_id).first()
    if product:
        return jsonify(id=product.id, name=product.name, price=product.price, stock=product.stock), 200
    return jsonify(message="Product not found"), 404

# Add product to cart
@app.route('/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json()
    product_id = data['product_id']
    quantity = data['quantity']

    # Check if product is in stock
    is_available, product = check_product_stock(product_id, quantity)
    if not is_available:
        return jsonify(message="Product is out of stock or insufficient stock available"), 400

    # Add item to the cart
    cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
    db.session.add(cart_item)
    product.stock -= quantity  # Decrease stock
    db.session.commit()

    return jsonify(message="Product added to cart"), 201

# Get user's cart
@app.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    cart = [{'product_id': item.product_id, 'product_name': item.product.name, 'quantity': item.quantity} for item in cart_items]
    return jsonify(cart=cart), 200

# Test route to list all products (for development/testing)
@app.route('/products', methods=['GET'])
def list_products():
    products = Product.query.all()
    product_list = [{'id': p.id, 'name': p.name, 'price': p.price, 'stock': p.stock} for p in products]
    return jsonify(products=product_list), 200

if __name__ == '__main__':
    app.run(debug=True)