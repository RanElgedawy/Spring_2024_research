from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ecommerce.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'super-secret-key')
jwt = JWTManager(app)
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('carts', lazy=True))
    product = db.relationship('Product', backref=db.backref('carts', lazy=True))

# Create tables and seed test data
with app.app_context():
    db.drop_all()
    db.create_all()

    
    # Seed test data
    if not User.query.filter_by(username='testuser').first():
        test_user = User(username='testuser')
        test_user.set_password('testpass')
        db.session.add(test_user)
    
    if not Product.query.first():
        products = [
            Product(name='Laptop', price=999.99, stock=10),
            Product(name='Phone', price=699.99, stock=15),
            Product(name='Tablet', price=299.99, stock=5)
        ]
        db.session.add_all(products)
    
    db.session.commit()

# Auth Routes
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and user.check_password(data.get('password')):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    
    return jsonify({"msg": "Invalid credentials"}), 401

# Product Routes
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"msg": "Product not found"}), 404
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'stock': product.stock
    })

# Cart Routes
@app.route('/cart/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Input validation
    if not all(key in data for key in ('product_id', 'quantity')):
        return jsonify({"msg": "Missing required fields"}), 400
    
    try:
        product_id = int(data['product_id'])
        quantity = int(data['quantity'])
    except ValueError:
        return jsonify({"msg": "Invalid input format"}), 400
    
    if quantity <= 0:
        return jsonify({"msg": "Quantity must be positive"}), 400
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"msg": "Product not found"}), 404
    
    if product.stock < quantity:
        return jsonify({"msg": "Insufficient stock"}), 400
    
    # Add to cart
    cart_item = Cart(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity
    )
    db.session.add(cart_item)
    db.session.commit()
    
    return jsonify({"msg": "Item added to cart", "item_id": cart_item.id}), 201

if __name__ == '__main__':
    app.run(debug=True)