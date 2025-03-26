from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # Change this in production!

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    carts = db.relationship('Cart', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    carts = db.relationship('Cart', backref='product', lazy=True)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Helper Functions
def product_exists(product_id):
    return Product.query.get(product_id) is not None

def stock_available(product_id, quantity):
    product = Product.query.get(product_id)
    return product.stock >= quantity if product else False

# API Endpoints
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'stock': product.stock
    })

@app.route('/api/cart/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id or not isinstance(quantity, int) or quantity < 1:
        return jsonify({'error': 'Invalid request'}), 400

    if not product_exists(product_id):
        return jsonify({'error': 'Product not found'}), 404

    if not stock_available(product_id, quantity):
        return jsonify({'error': 'Insufficient stock'}), 400

    user_id = get_jwt_identity()
    
    # Check if product already in cart
    existing = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    if existing:
        return jsonify({'error': 'Product already in cart'}), 400

    try:
        cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({'message': 'Product added to cart'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cart', methods=['GET'])
@jwt_required()
def view_cart():
    user_id = get_jwt_identity()
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    
    cart_data = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        cart_data.append({
            'product_id': product.id,
            'name': product.name,
            'price': product.price,
            'quantity': item.quantity,
            'added_at': item.created_at.isoformat()
        })
    
    return jsonify(cart_data)

# Authentication Endpoints
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    user = User.query.filter_by(username=username).first()
    if not user or user.password != password:  # In real-world use proper password hashing!
        return jsonify({"error": "Invalid credentials"}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token)

# Test Setup
def create_test_data():
    # Create test user
    test_user = User(username='testuser', password='testpass')
    db.session.add(test_user)
    
    # Create test product
    test_product = Product(name='Test Product', price=99.99, stock=10)
    db.session.add(test_product)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        if not User.query.first():  # Only create test data if DB is empty
            create_test_data()
    app.run(debug=True)
