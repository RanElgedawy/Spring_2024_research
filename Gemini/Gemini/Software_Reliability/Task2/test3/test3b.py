from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'  # Replace with your desired DB URL
db = SQLAlchemy(app)

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

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.json())
    return jsonify({'error': 'Product not found'}), 404

@app.route('/carts/<int:user_id>/add', methods=['POST'])
def add_to_cart(user_id):
    product_id = request.json.get('product_id')
    product = Product.query.get(product_id)
    if not product or product.stock <= 0:
        return jsonify({'error': 'Product not available'}), 400

    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = Cart(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(cart_item)

    db.session.commit()
    return jsonify({'message': 'Product added to cart'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # Add some sample products
    product1 = Product(name="Product 1", price=10.99, stock=5)
    product2 = Product(name="Product 2", price=19.99, stock=2)
    db.session.add_all([product1, product2])
    db.session.commit()

    # Test API endpoints
    response = requests.get('http://localhost:5000/products/1')
    print(response.json())

    response = requests.post('http://localhost:5000/carts/1/add', json={'product_id': 1})
    print(response.json())