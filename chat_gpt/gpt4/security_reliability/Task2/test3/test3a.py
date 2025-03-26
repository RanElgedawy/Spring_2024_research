from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
import os

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Foreign key from user table
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship('Product', backref='cart')

    __table_args__ = (CheckConstraint('quantity > 0', name='check_quantity_positive'),)


# Initialize DB and create tables
@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()

# API Endpoints

# 1. Retrieve product information by ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock
        }), 200
    return jsonify({'error': 'Product not found'}), 404

# 2. Add product to cart (only if in stock)
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')  # Assuming this is passed from an authenticated session or JWT
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Invalid product ID or quantity'}), 400

    product = Product.query.get(product_id)

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.stock < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Add product to cart
    cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
    db.session.add(cart_item)
    product.stock -= quantity  # Decrement stock
    db.session.commit()

    return jsonify({'message': f'{quantity} units of {product.name} added to cart'}), 200

# 3. Save the cart (optional)
@app.route('/cart/save', methods=['POST'])
def save_cart():
    user_id = request.json.get('user_id')
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400

    cart_data = [
        {'product_id': item.product_id, 'product_name': item.product.name, 'quantity': item.quantity}
        for item in cart_items
    ]
    
    return jsonify({'cart': cart_data}), 200

# To test the functionality
if __name__ == '__main__':
    app.run(debug=True)