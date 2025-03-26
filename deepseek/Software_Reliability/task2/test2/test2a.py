from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='_user_product_uc'),)

# Create tables and test data
with app.app_context():
    db.drop_all()
    db.create_all()
    
    # Add test users
    if not User.query.first():
        users = [
            User(username='john_doe'),
            User(username='jane_smith')
        ]
        db.session.bulk_save_objects(users)
    
    # Add test products
    if not Product.query.first():
        products = [
            Product(name='Wireless Headphones', description='Noise-canceling Bluetooth headphones', price=199.99, stock=10),
            Product(name='Smart Fitness Watch', description='Water-resistant fitness tracker', price=149.99, stock=5)
        ]
        db.session.bulk_save_objects(products)
    
    db.session.commit()

# API Endpoints
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'stock': product.stock
    })

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    # Get user from headers
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Missing user identification'}), 401
    
    # Validate user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Parse request data
    data = request.get_json()
    if not data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    product_id = data['product_id']
    quantity = data['quantity']
    
    # Validate quantity
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400
    
    # Validate product exists
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Check existing cart item
    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    requested_quantity = quantity + (cart_item.quantity if cart_item else 0)
    
    # Validate stock
    if requested_quantity > product.stock:
        return jsonify({'error': 'Insufficient stock'}), 400
    
    # Update or create cart item
    if cart_item:
        cart_item.quantity = requested_quantity
    else:
        cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    return jsonify({'message': 'Product added to cart successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)