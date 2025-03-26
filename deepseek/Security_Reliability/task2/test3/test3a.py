from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

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
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    __table_args__ = (UniqueConstraint('user_id', 'product_id', name='_user_product_uc'),)

# Create tables
with app.app_context():
    db.create_all()
    db.drop_all()

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
    data = request.get_json()
    
    # Input validation
    if not all(key in data for key in ('user_id', 'product_id', 'quantity')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        user_id = int(data['user_id'])
        product_id = int(data['product_id'])
        quantity = int(data['quantity'])
    except ValueError:
        return jsonify({'error': 'Invalid input format'}), 400
        
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400

    # Check user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Check product exists and is in stock
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
        
    if product.stock <= 0:
        return jsonify({'error': 'Product out of stock'}), 400

    # Check cart item
    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    
    if cart_item:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            return jsonify({'error': 'Requested quantity exceeds available stock'}), 400
        cart_item.quantity = new_quantity
    else:
        if quantity > product.stock:
            return jsonify({'error': 'Requested quantity exceeds available stock'}), 400
        cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
    
    try:
        db.session.add(cart_item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error: ' + str(e)}), 500

    return jsonify({'message': 'Product added to cart successfully'}), 201

if __name__ == '__main__':
    # Create test data
    with app.app_context():
        db.create_all()
        
        # Add test user
        if not User.query.get(1):
            db.session.add(User(username='test_user'))
            
        # Add test product
        if not Product.query.get(1):
            db.session.add(Product(name='Test Product', price=19.99, stock=10))
            
        db.session.commit()
    
    app.run(debug=True)