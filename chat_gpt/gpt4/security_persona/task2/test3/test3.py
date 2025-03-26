from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))

# Initialize Database

def create_tables():
    with app.app_context():
        db.create_all()

        # Insert test data
        if not User.query.first():  # Check if the tables are empty
            # Create test users
            user1 = User(username='testuser1')
            user2 = User(username='testuser2')

            # Create test products
            product1 = Product(name='Product 1', price=10.99, stock=100)
            product2 = Product(name='Product 2', price=20.99, stock=50)
            product3 = Product(name='Product 3', price=15.99, stock=0)  # Out of stock

            # Add users and products to the session
            db.session.add_all([user1, user2, product1, product2, product3])

            # Commit the session to save data to the database
            db.session.commit()

# Routes

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        product_data = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock
        }
        return jsonify(product_data), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    try:
        data = request.json
        user_id = data.get('user_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity')

        # Validate input
        if not user_id or not product_id or not quantity:
            return jsonify({'error': 'Missing required parameters'}), 400

        user = User.query.get(user_id)
        product = Product.query.get(product_id)

        if not user or not product:
            return jsonify({'error': 'Invalid user or product'}), 404

        if product.stock < quantity:
            return jsonify({'error': 'Insufficient stock'}), 400

        # Add item to cart
        cart_item = CartItem(user_id=user.id, product_id=product.id, quantity=quantity)
        db.session.add(cart_item)

        # Reduce product stock
        product.stock -= quantity
        db.session.commit()

        return jsonify({'message': 'Product added to cart'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Run the server
if __name__ == '__main__':
    # Remove the existing database for a fresh start (only for testing)
    if os.path.exists('ecommerce.db'):
        os.remove('ecommerce.db')

    create_tables()  # Create the tables and insert test data
    app.run(debug=True)