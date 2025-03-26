from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Using a local SQLite database for simplicity.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), nullable=False, unique=True)
    items = db.relationship('CartItem', backref='cart', lazy=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product = db.relationship('Product')

# Create tables and insert sample product data if not already present.
with app.app_context():
    db.drop_all()
    db.create_all()
    if Product.query.count() == 0:
        sample_products = [
            Product(name="Laptop", description="Gaming Laptop", price=1200.00, stock=5),
            Product(name="Smartphone", description="Latest Smartphone", price=800.00, stock=10),
            Product(name="Headphones", description="Noise-cancelling headphones", price=150.00, stock=0)
        ]
        db.session.bulk_save_objects(sample_products)
        db.session.commit()

# API Endpoint to retrieve product information by product ID
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
        return jsonify({'error': 'Product not found'}), 404

# API Endpoint to add a product to the user's cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    # Simulate authentication by reading a user id from a header.
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401

    data = request.get_json()
    if not data or 'product_id' not in data:
        return jsonify({'error': 'Product ID is required'}), 400

    product_id = data['product_id']
    quantity = data.get('quantity', 1)
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.stock < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400

    # Get or create a cart for the user.
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()

    # Check if the product is already in the cart; update quantity if it is.
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)

    # Optionally, reduce product stock to reflect items added to the cart.
    product.stock -= quantity

    db.session.commit()
    return jsonify({'message': 'Product added to cart successfully'})

# Testing endpoint to view the user's cart.
@app.route('/cart', methods=['GET'])
def view_cart():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401

    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart or not cart.items:
        return jsonify({'cart': []})
    
    cart_items = []
    for item in cart.items:
        cart_items.append({
            'product_id': item.product_id,
            'name': item.product.name,
            'quantity': item.quantity,
            'price': item.product.price
        })
    return jsonify({'cart': cart_items})

if __name__ == '__main__':
    # Run the Flask development server.
    app.run(debug=True)
