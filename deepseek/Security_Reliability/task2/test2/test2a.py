from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    api_key = db.Column(db.String(120), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        CheckConstraint('stock >= 0', name='stock_non_negative'),
    )

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        CheckConstraint('quantity > 0', name='quantity_positive'),
        db.UniqueConstraint('user_id', 'product_id', name='unique_user_product'),
    )

# Initialize database with test data
with app.app_context():
    db.drop_all()
    db.create_all()
    
    # Create test user if not exists
    if not User.query.filter_by(username='test_user').first():
        test_user = User(username='test_user', api_key='secure_key_123')
        db.session.add(test_user)
    
    # Create test products if not exist
    if not Product.query.count():
        products = [
            Product(name='Wireless Mouse', price=29.99, stock=50),
            Product(name='Mechanical Keyboard', price=99.99, stock=25),
            Product(name='Gaming Monitor', price=299.99, stock=10)
        ]
        db.session.bulk_save_objects(products)
    
    db.session.commit()

# Helper Functions
def authenticate_user(api_key):
    return User.query.filter_by(api_key=api_key).first()

# API Endpoints
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'stock': product.stock
    })

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    # Authentication
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({'error': 'Missing API key'}), 401
    
    user = authenticate_user(api_key)
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Request validation
    data = request.get_json()
    if not data or 'product_id' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    product_id = data['product_id']
    quantity = data.get('quantity', 1)

    if quantity < 1:
        return jsonify({'error': 'Quantity must be at least 1'}), 400

    # Product validation
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Stock validation
    cart_item = Cart.query.filter_by(
        user_id=user.id, 
        product_id=product.id
    ).first()

    current_quantity = cart_item.quantity if cart_item else 0
    requested_total = current_quantity + quantity

    if requested_total > product.stock:
        return jsonify({
            'error': f'Only {product.stock - current_quantity} items available'
        }), 400

    # Update cart
    if cart_item:
        cart_item.quantity = requested_total
    else:
        cart_item = Cart(
            user_id=user.id,
            product_id=product.id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()

    return jsonify({
        'message': 'Product added to cart',
        'cart_item': {
            'product_id': product.id,
            'quantity': requested_total
        }
    })

# Test Client
if __name__ == '__main__':
    app.run(debug=True)