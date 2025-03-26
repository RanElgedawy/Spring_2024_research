from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'  # Replace with your desired DB URI
db = SQLAlchemy(app)

# Model definitions
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    quantity_in_stock = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='carts')

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, nullable=False)
    cart = db.relationship('Cart', backref='items')
    product = db.relationship('Product', backref='cart_items')

# API endpoints
@app.route('/api/products/<int:product_id>')
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.to_dict())
    return jsonify({'error': 'Product not found'}), 404

@app.route('/api/carts/<int:user_id>/add', methods=['POST'])
def add_to_cart(user_id):
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)

    product = Product.query.get(product_id)
    if not product or product.quantity_in_stock < quantity:
        return jsonify({'error': 'Product is out of stock'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    cart = user.carts[0] if user.carts else Cart(user_id=user_id)
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        cart.items.append(cart_item)

    db.session.add(cart)
    db.session.commit()

    return jsonify({'message': 'Product added to cart'})

# ... other API endpoints for cart management, user authentication, etc.

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    app.run(debug=True)