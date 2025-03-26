from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the database models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    carts = db.relationship('Cart', backref='user', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    products = db.relationship('CartItem', backref='cart', lazy=True)

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# Create all the tables
with app.app_context():
    db.create_all()

# API route to retrieve product information by product ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock
        })
    else:
        return jsonify({'message': 'Product not found'}), 404

# API route to add product to the user's cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    # Validate inputs
    user = User.query.get(user_id)
    product = Product.query.get(product_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    if product.stock < quantity:
        return jsonify({'message': 'Not enough stock'}), 400

    # Check if the user already has a cart, if not create one
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()

    # Check if the product is already in the cart, update quantity if it is
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)

    # Deduct stock from the product
    product.stock -= quantity

    # Commit the changes
    db.session.commit()

    return jsonify({'message': 'Product added to cart successfully'})

# API route to view the user's cart
@app.route('/cart/<int:user_id>', methods=['GET'])
def view_cart(user_id):
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        return jsonify({'message': 'Cart not found'}), 404

    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    items = [{
        'product_id': item.product_id,
        'quantity': item.quantity,
        'product_name': Product.query.get(item.product_id).name,
        'product_price': Product.query.get(item.product_id).price
    } for item in cart_items]

    return jsonify({'cart': items})

# For testing purposes, we will create some users and products
@app.route('/setup', methods=['POST'])
def setup():
    # Add a couple of users
    user1 = User(username="user1")
    user2 = User(username="user2")
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()

    # Add a few products
    product1 = Product(name="Laptop", description="A powerful laptop", price=1200.99, stock=10)
    product2 = Product(name="Headphones", description="Noise-cancelling headphones", price=199.99, stock=25)
    db.session.add(product1)
    db.session.add(product2)
    db.session.commit()

    return jsonify({'message': 'Setup complete'})

if __name__ == '__main__':
    app.run(debug=True)