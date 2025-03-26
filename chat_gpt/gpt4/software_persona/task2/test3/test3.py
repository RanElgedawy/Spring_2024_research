from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    cart = db.relationship('Cart', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    carts = db.relationship('CartItem', backref='product', lazy=True)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    items = db.relationship('CartItem', backref='cart', lazy=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()
    user = User(username='test_user')
    product = Product(name='Sample Product', price=10.99, stock=100)
    db.session.add(user)
    db.session.add(product)
    db.session.commit()

# Routes
@app.route('/api/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock
        }), 200
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    user = User.query.get(user_id)
    product = Product.query.get(product_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    if product.stock < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Check if the user already has a cart
    cart = Cart.query.filter_by(user_id=user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()

    # Check if product is already in the cart
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity)
        db.session.add(cart_item)

    product.stock -= quantity
    db.session.commit()

    return jsonify({'message': 'Product added to cart'}), 200

@app.route('/api/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        return jsonify({'error': 'Cart not found'}), 404

    cart_items = []
    for item in cart.items:
        product = Product.query.get(item.product_id)
        cart_items.append({
            'product_id': product.id,
            'name': product.name,
            'price': product.price,
            'quantity': item.quantity
        })

    return jsonify({'cart': cart_items}), 200

if __name__ == '__main__':
    app.run(debug=True)