from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import jwt
import datetime

# Initialize Flask app
app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # This should be more secure in production

db = SQLAlchemy(app)

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500))
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# Function to create the database tables
@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()

# Utility function to verify JWT token and retrieve user
def decode_token(token):
    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user = User.query.filter_by(id=decoded_token['user_id']).first()
        return user
    except Exception as e:
        return None

# API to retrieve product information by ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock
        }), 200
    else:
        return jsonify({'message': 'Product not found'}), 404

# API to add products to the user's cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    # Check for valid token (authentication)
    token = request.headers.get('Authorization').split(" ")[1]
    user = decode_token(token)
    
    if not user:
        return jsonify({'message': 'Invalid or missing token'}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    if product.stock < quantity:
        return jsonify({'message': 'Not enough stock available'}), 400
    
    # Add product to cart
    existing_cart_item = Cart.query.filter_by(user_id=user.id, product_id=product.id).first()
    
    if existing_cart_item:
        existing_cart_item.quantity += quantity
    else:
        new_cart_item = Cart(user_id=user.id, product_id=product.id, quantity=quantity)
        db.session.add(new_cart_item)
    
    # Decrease stock of the product
    product.stock -= quantity
    
    db.session.commit()
    
    return jsonify({'message': f'Added {quantity} of {product.name} to your cart'}), 200

# Utility function to generate a JWT token for testing
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")

# Route to test token generation (for testing purposes)
@app.route('/login/<int:user_id>', methods=['GET'])
def login(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    token = generate_token(user.id)
    return jsonify({'token': token})

# Test data setup
@app.route('/setup', methods=['GET'])
def setup():
    # Create some sample users
    if not User.query.first():
        user1 = User(username='john_doe')
        user2 = User(username='jane_smith')
        db.session.add_all([user1, user2])
        db.session.commit()

    # Create some sample products
    if not Product.query.first():
        product1 = Product(name='Laptop', description='A powerful laptop', price=999.99, stock=10)
        product2 = Product(name='Smartphone', description='A high-end smartphone', price=799.99, stock=5)
        db.session.add_all([product1, product2])
        db.session.commit()

    return jsonify({'message': 'Test data created'}), 200

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)