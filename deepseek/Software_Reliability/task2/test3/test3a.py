from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    token = db.Column(db.String(100), unique=True, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables and insert sample data
with app.app_context():
    db.drop_all()
    db.create_all()
    # Insert sample products if they don't exist
    if not Product.query.get(1):
        product1 = Product(id=1, name='Laptop', price=999.99, stock=10)
        product2 = Product(id=2, name='Phone', price=699.99, stock=5)
        db.session.add(product1)
        db.session.add(product2)
    # Insert test user
    if not User.query.get(1):
        user = User(id=1, username='testuser', token='testtoken123')
        db.session.add(user)
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
        'price': product.price,
        'stock': product.stock
    })

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    # User authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid authorization header'}), 401
    token = auth_header.split(' ')[1]
    user = User.query.filter_by(token=token).first()
    if not user:
        return jsonify({'error': 'Invalid token'}), 401

    # Validate request data
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Invalid product ID or quantity'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.stock <= 0:
        return jsonify({'error': 'Product out of stock'}), 400

    # Add/update cart item
    cart_item = Cart.query.filter_by(
        user_id=user.id, 
        product_id=product.id
    ).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(
            user_id=user.id,
            product_id=product.id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()

    return jsonify({'message': 'Product added to cart successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)