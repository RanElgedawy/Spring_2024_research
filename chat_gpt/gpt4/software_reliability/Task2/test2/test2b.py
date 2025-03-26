from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# SQLite Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    carts = db.relationship('Cart', backref='user', lazy=True)

# Define the Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)  # Track stock availability

# Define the Cart model
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# Create the tables
db.drop_all()
db.create_all()

# Route to retrieve product information by product ID
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
    else:
        return jsonify({'error': 'Product not found'}), 404

# Route to add a product to a user's cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
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

    # Add product to cart
    existing_cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if existing_cart_item:
        existing_cart_item.quantity += quantity
    else:
        new_cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(new_cart_item)

    # Update product stock
    product.stock -= quantity
    db.session.commit()

    return jsonify({'message': 'Product added to cart'}), 200

# Route to view user's cart
@app.route('/cart/<int:user_id>', methods=['GET'])
def view_cart(user_id):
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    if not cart_items:
        return jsonify({'message': 'Cart is empty'}), 200

    cart_data = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        cart_data.append({
            'product_id': product.id,
            'product_name': product.name,
            'price': product.price,
            'quantity': item.quantity
        })

    return jsonify(cart_data), 200

# Test data setup for initial products and users
@app.before_first_request
def create_test_data():
    db.drop_all()  # Reset database (for testing)
    db.create_all()

    # Add test users
    user1 = User(username="user1")
    user2 = User(username="user2")
    db.session.add(user1)
    db.session.add(user2)

    # Add test products
    product1 = Product(name="Laptop", price=1000.00, stock=10)
    product2 = Product(name="Smartphone", price=500.00, stock=5)
    product3 = Product(name="Headphones", price=150.00, stock=20)
    db.session.add(product1)
    db.session.add(product2)
    db.session.add(product3)

    db.session.commit()

# Run the app
if __name__ == '__main__':
    app.run(debug=True)