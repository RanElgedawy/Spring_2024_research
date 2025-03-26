from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import unittest

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
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    in_stock = db.Column(db.Boolean, default=True, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='unique_user_product'),
    )

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
        'in_stock': product.in_stock
    })

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required_fields = ['user_id', 'product_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        user_id = int(data['user_id'])
        product_id = int(data['product_id'])
        quantity = int(data.get('quantity', 1))
    except ValueError:
        return jsonify({'error': 'Invalid input format'}), 400

    if quantity < 1:
        return jsonify({'error': 'Invalid quantity'}), 400

    # Validate user exists
    if not User.query.get(user_id):
        return jsonify({'error': 'User not found'}), 404

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if not product.in_stock:
        return jsonify({'error': 'Product out of stock'}), 400

    # Update or create cart entry
    cart_item = Cart.query.filter_by(
        user_id=user_id,
        product_id=product_id
    ).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)

    db.session.commit()

    return jsonify({'message': 'Item added to cart successfully'}), 201

# Test Suite
class TestEcommerceAPI(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        with app.app_context():
            db.drop_all()
            db.create_all()
            # Create test data
            test_user = User(id=1, username='testuser')
            db.session.add(test_user)
            db.session.add(Product(id=1, name='Test Product', price=9.99, in_stock=True))
            db.session.add(Product(id=2, name='Out of Stock Product', price=19.99, in_stock=False))
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def test_get_product(self):
        response = self.client.get('/products/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['name'], 'Test Product')

    def test_add_to_cart_valid(self):
        response = self.client.post('/cart/add', json={
            'user_id': 1,
            'product_id': 1,
            'quantity': 2
        })
        self.assertEqual(response.status_code, 201)

    def test_add_to_cart_out_of_stock(self):
        response = self.client.post('/cart/add', json={
            'user_id': 1,
            'product_id': 2
        })
        self.assertEqual(response.status_code, 400)

    def test_add_to_cart_invalid_user(self):
        response = self.client.post('/cart/add', json={
            'user_id': 999,
            'product_id': 1
        })
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    unittest.main()