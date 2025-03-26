from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
import unittest

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app)

# Database Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship('Product', backref='carts')

# Create tables and sample data
with app.app_context():
    db.create_all()
    if not Product.query.first():
        sample_product = Product(name='Wireless Mouse', price=29.99, stock=10)
        db.session.add(sample_product)
        db.session.commit()

# API Resources
class ProductResource(Resource):
    def get(self, product_id):
        product = Product.query.get(product_id)
        if not product:
            return {'message': 'Product not found'}, 404
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock
        })

class CartAddResource(Resource):
    def post(self):
        data = request.get_json()
        required_fields = ['user_id', 'product_id', 'quantity']
        
        # Input validation
        if not all(field in data for field in required_fields):
            return {'message': 'Missing required fields'}, 400
        
        try:
            user_id = int(data['user_id'])
            product_id = int(data['product_id'])
            quantity = int(data['quantity'])
        except ValueError:
            return {'message': 'Invalid data types'}, 400

        if quantity <= 0:
            return {'message': 'Quantity must be positive'}, 400

        product = Product.query.get(product_id)
        if not product:
            return {'message': 'Product not found'}, 404

        if quantity > product.stock:
            return {'message': 'Insufficient stock'}, 400

        # Check existing cart item
        existing_item = Cart.query.filter_by(
            user_id=user_id, 
            product_id=product_id
        ).first()

        if existing_item:
            new_quantity = existing_item.quantity + quantity
            if new_quantity > product.stock:
                return {'message': 'Exceeds available stock'}, 400
            existing_item.quantity = new_quantity
        else:
            new_item = Cart(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(new_item)

        db.session.commit()
        return {'message': 'Item added to cart successfully'}, 200

api.add_resource(ProductResource, '/product/<int:product_id>')
api.add_resource(CartAddResource, '/cart/add')

# Testing
class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            db.create_all()
            product = Product(name='Test Product', price=9.99, stock=5)
            db.session.add(product)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_product(self):
        response = self.app.get('/product/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Product', response.data)

    def test_add_to_cart_valid(self):
        data = {'user_id': 1, 'product_id': 1, 'quantity': 2}
        response = self.app.post('/cart/add', json=data)
        self.assertEqual(response.status_code, 200)

    def test_add_to_cart_insufficient_stock(self):
        data = {'user_id': 1, 'product_id': 1, 'quantity': 6}
        response = self.app.post('/cart/add', json=data)
        self.assertEqual(response.status_code, 400)

    def test_add_to_cart_invalid_product(self):
        data = {'user_id': 1, 'product_id': 999, 'quantity': 1}
        response = self.app.post('/cart/add', json=data)
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    # Run tests if executed directly
    unittest.main(argv=[''], exit=False)
    
    # Start the development server
    app.run(debug=True)