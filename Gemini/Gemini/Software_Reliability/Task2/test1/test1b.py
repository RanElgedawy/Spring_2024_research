from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify

db = SQLAlchemy()

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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db.init_app(app)

@app.route('/product/<int:product_id>')
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.serialize())
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    product_id = request.json.get('product_id')
    user_id = request.json.get('user_id')  # Assuming user_id is provided in the request

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.stock == 0:
        return jsonify({'error': 'Product out of stock'}), 400

    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(cart_item)

    db.session.commit()
    return jsonify({'message': 'Product added to cart'})

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        user1 = User(username="test_user1")
        user2 = User(username="test_user2")
        db.session.add(user1)
        db.session.add(user2)

        # Create test products
        product1 = Product(name="Product 1", price=19.99, stock=5)
        product2 = Product(name="Product 2", price=24.99, stock=3)
        db.session.add(product1)
        db.session.add(product2)

        db.session.commit()
    app.run(debug=True)