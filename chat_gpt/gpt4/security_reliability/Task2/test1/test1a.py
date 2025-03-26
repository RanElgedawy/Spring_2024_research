from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import CheckConstraint

app = Flask(__name__)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'  # Change to MySQL if needed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'  # Needed for secure session management

# Initialize the database
db = SQLAlchemy(app)

# Database Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # For simplicity, storing as plain text (use hashing)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    db.CheckConstraint('quantity > 0')

# Create the database tables if they don't exist
@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()

# Helper function to validate authentication
def authenticate_user(user_id):
    # In a real application, you'd use session or token-based auth
    user = User.query.get(user_id)
    if user:
        return True
    return False

# API Routes

# 1. Retrieve product info by product ID
@app.route('/api/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock
        })
    else:
        return jsonify({'error': 'Product not found'}), 404

# 2. Add product to cart
@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity')

    if not authenticate_user(user_id):
        return jsonify({'error': 'Unauthorized access'}), 401

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.stock < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Add to cart
    try:
        new_cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(new_cart_item)
        product.stock -= quantity  # Update the product stock
        db.session.commit()
        return jsonify({'success': 'Product added to cart successfully'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Could not add product to cart'}), 400

# 3. Save cart to database (optional: You can add a checkout mechanism here)
@app.route('/api/cart/save', methods=['POST'])
def save_cart():
    user_id = request.json.get('user_id')

    if not authenticate_user(user_id):
        return jsonify({'error': 'Unauthorized access'}), 401

    # You can implement saving or checkout mechanism here
    return jsonify({'success': 'Cart saved successfully'})

# 4. List items in a user's cart
@app.route('/api/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    if not authenticate_user(user_id):
        return jsonify({'error': 'Unauthorized access'}), 401

    cart_items = Cart.query.filter_by(user_id=user_id).all()
    result = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        result.append({
            'product_id': product.id,
            'product_name': product.name,
            'quantity': item.quantity,
            'price': product.price
        })

    return jsonify(result)

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)