from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500))
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))

# Initialize the database with tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Endpoint to retrieve product information by product ID
@app.route('/api/product/<int:product_id>', methods=['GET'])
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

# Endpoint to add a product to the user's cart
@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)

    # Check if user and product exist
    user = User.query.get(user_id)
    product = Product.query.get(product_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.stock < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Add the product to the user's cart
    cart_item = CartItem(user_id=user.id, product_id=product.id, quantity=quantity)
    db.session.add(cart_item)
    
    # Reduce the product stock
    product.stock -= quantity

    db.session.commit()

    return jsonify({'message': 'Product added to cart successfully'})

# Testing endpoint: Create some test data
@app.route('/api/test/create_data', methods=['POST'])
def create_test_data():
    # Create users
    user1 = User(username="user1")
    user2 = User(username="user2")
    
    # Create products
    product1 = Product(name="Product 1", description="Description of product 1", price=9.99, stock=10)
    product2 = Product(name="Product 2", description="Description of product 2", price=19.99, stock=5)
    
    db.session.add(user1)
    db.session.add(user2)
    db.session.add(product1)
    db.session.add(product2)
    
    db.session.commit()

    return jsonify({'message': 'Test data created successfully'})

if __name__ == '__main__':
    app.run(debug=True)